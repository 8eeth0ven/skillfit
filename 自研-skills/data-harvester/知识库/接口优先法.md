# 接口优先法：能走 API 就不渲染

接口请求量小、结构化、好翻页，优先级永远高于开浏览器。本文命令基于 rg + curl + python3，可直接跑。

## §1 JS bundle 抽 API

### 1.1 找 bundle 文件

```bash
curl -s https://example.com/ -o /tmp/index.html
rg -oN 'src="[^"]+\.js[^"]*"' /tmp/index.html -r '$1'        # script 标签
```

### 1.2 五组正则抽接口（按命中质量排序，注释在行尾可直接跑）

```bash
rg -oN 'https?://[A-Za-z0-9._~:/?#@!$&+,;=%-]{8,}' bundle.js | sort -u | rg -v '\.(png|jpg|svg|woff|css|js)$'   # ①绝对URL，看跨域网关
rg -oN '["`](/(api|apis|v[1-9]|gw|gateway|service|mvc|action|rest)/[A-Za-z0-9_/.-]+)["`]' bundle.js -r '$1' | sort -u   # ②相对路径API，前缀按目标站扩
rg -oN 'fetch\(["`][^"`]+["`]' bundle.js | sort -u   # ③fetch 调用点
rg -oN '(axios\.(get|post)|\$\.ajax)\(["`][^"`]+["`]' bundle.js | sort -u   # ④axios 调用点，URL 在第一参
rg -oN '(baseURL|BASE_URL|apiBase|API_PREFIX)["`]?\s*[:=]\s*["`][^"`]+["`]' bundle.js   # ⑤base+path 拼接型，找 base 定义
```

webpack 打包后字符串不碎，①② 通常直接出全量接口清单；抽完和 §2 network 对照筛出真正出数据的。

### 1.3 source map 还原（有 .map 才用）

```bash
tail -c 300 bundle.js | rg -oN 'sourceMappingURL=\S+'    # 确认有没有 map
curl -s -o bundle.js.map https://example.com/static/js/app.8f3c2.js.map
jq -r '.sources[]' bundle.js.map                          # src/api/ 下就是接口层
jq -r '.sourcesContent[]?' bundle.js.map | rg -oN '"/[A-Za-z0-9_/.-]+"' | sort -u   # 源码里的路径全量
```

上线没带 map 就跳过本节，不要硬逆向混淆代码——先回 §2 看网络请求更快。

## §2 network 面板对照法

目标：从一堆 XHR 里定位「返回目标数据」的那一个。步骤：

1. 浏览器 F12 → Network → Fetch/XHR 过滤 → 刷新页面 → 列表出现数据时停
2. 按类型排序找响应体最大的 JSON；右键 Copy → Copy as cURL（含全部头和 Cookie）
3. 本地复现：粘过来加 `-s -o /tmp/r.json -w '%{http_code}'` 跑，`jq` 验字段

### 2.1 复现时的裁剪顺序（留最少的头）

| 裁剪 | 做法 | 何时停 |
|------|------|--------|
| Header | 从 copy-as-curl 全量开始，每次删 1 个重放 | 删到报错为止，剩下的就是必需头（常见只需 UA/Referer/Accept） |
| Cookie | 同上逐个删 | 很多公开接口根本不要 Cookie；要的记下是哪个键 |
| 参数 | URL query 逐个删 | 定出必需参数，多余的（埋点 id）扔掉 |

### 2.2 python 复现模板

```python
import requests

s = requests.Session()
s.headers.update({
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Referer": "https://example.com/list",
    "Accept": "application/json, text/plain, */*",
})
r = s.get("https://example.com/api/items", params={"page": 1, "pageSize": 20}, timeout=15)
r.raise_for_status()
items = r.json()["data"]["list"]   # 路径按实际响应调整，先 print(r.json()) 看
print(len(items))
```

## §3 分页三型与终止判定

| 型 | 请求特征 | 响应特征 | 翻页动作 | 终止判定 |
|----|---------|---------|---------|---------|
| page 型 | `page=2&pageSize=20`（或 `pageNum/pageNo`） | 常带 `total` | page+=1 | 返回条数 < pageSize，或 page*pageSize ≥ total |
| offset 型 | `offset=40&limit=20`（或 `start/skip`） | 可无 total | offset+=limit | 返回条数 < limit；连续 2 页空 |
| cursor 型 | `after=eyJ...` / `next_cursor` 参数 | 带 `next_cursor`/`has_more`/`nextPageToken` | 用响应里的新 cursor | has_more 为 false/缺省，或 cursor 为空/与上轮相同 |

### 3.1 终止保险丝（防漏页防死循环）

```python
seen = set()
while True:
    data = fetch(page=page, offset=offset, cursor=cursor); items = data["list"]
    if len(items) == 0: break                      # 空页即停（有 total 的用 total 双保险）
    write_jsonl(items)
    if pager_type == "cursor":
        cursor = data["next_cursor"]
        if not cursor or cursor in seen: break     # cursor 回环 = 死循环，立刻停
        seen.add(cursor)
    page, offset = page + 1, offset + limit
    if page > 5000: break                          # 深度保险丝，防参数失效后无限翻
    time.sleep(random.uniform(1.5, 3))
```

### 3.2 边界陷阱

| 陷阱 | 判定 | 处理 |
|------|------|------|
| 末页仍返回满页 | 请求 page=9999 看返回什么 | 返回首页数据 → 必须 total 截断；返回空 → 空即停 |
| pageSize 可调 | 试 `pageSize=100` | 允许就调大（100 内），减少请求次数；报错就回默认 |
| 排序不稳定致翻页重复/丢条 | 对比第 2 页首条是否 == 第 1 页末条 | 加稳定排序参数（如 `orderBy=id`）或改 cursor 型 |
| 软删数据导致 total 对不上 | 采完 count ≠ total | 台账记差值即可，不硬凑 |

## §4 列表→详情→附件三段式

```
段1 列表页翻页 → 只抽 id + 列表字段 → 写 items.jsonl（status=list）
段2 详情接口逐条 → 用 id 拼 /api/item/{id} → 补全字段 → 更新同一条（或另存 detail.jsonl）
段3 附件下载 → 详情里的 fileUrl → 下载到 files/，台账记 url→本地路径
```

要点：

1. **队列驱动**：段 1 产出的 id 集合就是段 2 的任务队列；断点 = 已完成 id 集合（state.json 的 done_urls）。
2. **三段速率独立**：附件常在不同域（OSS/CDN），速率可单独放宽；OSS 链接带签名过期参数的，抓到就立刻下载，不要存进队列隔天用。
3. **详情失败不阻塞**：单条详情 3 次失败记台账跳过，列表数据已保住。

```python
for it in pending_items:                       # pending = 全量 id - done_urls
    d = s.get(f"{BASE}/api/item/{it['id']}", timeout=15).json()
    it.update(d["data"]); append_jsonl("detail.jsonl", it)
    mark_done(it["id"]); time.sleep(random.uniform(1, 2))   # 每条完成即写 state
```

## §5 签名接口静态分析

特征：请求带 `_t`/`timestamp`/`nonce`/`sign`/`token` 参数，或响应 `{"code":401,"msg":"签名错误/已过期"}`。

### 5.1 定位签名代码

```bash
rg -oN ".{60}(sign|signature)[\"']?\s*[:=][^,;}]{0,80}" bundle.js | head -20   # ①从参数名找赋值处
rg -oN ".{40}(timestamp|_t|nonce)[\"']?\s*[:=]\s*[^,;}]{0,50}" bundle.js | head -10
rg -oN '(md5|sha1|sha256|hmac|CryptoJS|JSEncrypt|AES|DES)\w*' bundle.js | sort | uniq -c | sort -rn | head   # ②哈希函数特征，打包后字面量仍在
rg -oN "(signKey|secret|salt|appkey|app_key|appId)[\"']?\s*[:=]\s*[\"\`][A-Za-z0-9_-]{6,}[\"\`]" bundle.js   # ③找盐
```

### 5.2 常见签名模式与复现

| 模式 | 特征 | 复现 |
|------|------|------|
| 参数排序 + 盐 + md5 | 代码里出现 `sort()` 后 `join('')` | python：`hashlib.md5((''.join(f'{k}{v}' for k,v in sorted(params.items()))+SALT).encode()).hexdigest()` |
| 时间戳参与 | sign 里含 `Date.now()` | 每次请求现算，过期一般 5 分钟，失败先比对服务器时间偏移 |
| AES/DES 加密参数 | CryptoJS.AES.encrypt | 把该函数原样抠出存 sign.js，`node -e` 调用取值 |
| 复杂混淆 | rg 追不到 | 放弃静态，node 直接 `require('./bundle.js')` 执行其加密函数，或改走渲染拦响应 |

抠函数跑法：`node -e 'const {sign}=require("/tmp/bundle.js"); console.log(sign({page:1}))'`（导出名从调用点上下文抄）。**10 分钟内复现不了就切换通道**（渲染与反爬 §1），不在混淆代码上恋战。

## §6 GraphQL 批量查询

特征：所有请求都 POST 同一个 `/graphql` 端点，请求体含 `query`/`operationName`/`variables`。

### 6.1 认清结构

```bash
rg -oN '(query|mutation)\s+\w+\s*[({][^`}]{0,200}' bundle.js | head -10   # 模板字符串里的查询原样保留
rg -oN "operationName[\"']?\s*[:=]\s*[\"\`]\w+" bundle.js | sort -u           # 站内已用的操作名全量
```

### 6.2 翻页（cursor 通常在 page info 里）

```python
q = """query($after:String){ items(first:50, after:$after){
  edges{node{id title updatedAt}} pageInfo{hasNextPage endCursor} } }"""
after = None
while True:
    d = s.post(GQL, json={"query": q, "variables": {"after": after}}).json()
    edge = d["data"]["items"]
    write_jsonl([e["node"] for e in edge["edges"]])
    if not edge["pageInfo"]["hasNextPage"]: break
    after = edge["pageInfo"]["endCursor"]; time.sleep(1.5)
```

### 6.3 alias 批量（一次请求取多页/多对象，减请求数）

```json
{"query": "{ p1: items(page:1, size:50){id title} p2: items(page:2, size:50){id title} }"}
```

注意：单请求节点数有上限（常 100k 字节或字段数限制），批 5–10 页试探；服务端限深度时拆小。响应按 alias 分键取数。
