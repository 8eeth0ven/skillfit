# 渲染与反爬：浏览器是最后手段

先判定、再等待、后放弃。本文明线：验证码=停止，盾重试 2 次即弃，不为对抗加机器。

## §1 何时上 Playwright（判定树）

```
curl 拿首页
 ├─ HTML 里已有目标数据（rg '<title>|关键字' 命中）→ 纯静态，BeautifulSoup 解析，结束
 ├─ 命中初始状态 JSON ↓（优先抽 JSON，不开浏览器）
 │    rg -oN '__NEXT_DATA__|__NUXT__|__INITIAL_STATE__|window\.__[A-Z_]+__' /tmp/index.html
 │    → python 正则抠 <script id="__NEXT_DATA__"> 内容 → json.loads 直接得全量数据
 ├─ 都没有 → 接口优先法 §1 抽 bundle → curl 能复现数据接口 → 走 HTTP，结束
 └─ 接口带盾/签名复现不出/数据真靠 JS 执行才生成 → 上 Playwright（本文件）
```

初始状态 JSON 一旦命中，翻页常也能找到对应接口（数据不可能只塞第一页），先回 接口优先法 §2。

## §2 等待策略

| 写法 | 用法 | 适用 | 陷阱 |
|------|------|------|------|
| `domcontentloaded` | `page.goto(url, wait_until="domcontentloaded")` | 默认首选，最快 | DOM 好了数据没到，必须再配元素/接口等待 |
| 具体元素 | `page.wait_for_selector(".item-card", timeout=10000)` | 知道数据长什么样子 | 类名是 CSS hash 的会变，选内容型选择器（`[class*=item]`） |
| 等接口 | `page.wait_for_response(lambda r: "/api/items" in r.url, timeout=15000)` | 最可靠：数据到即到 | 接口名未知时先开一次页面用 `page.on("response")` 记录 |
| `networkidle` | — | **不可用时**（新版 Playwright 对单页应用永远等不到 idle） | 别硬等；用「等接口 + 兜底 sleep 3s」替代 |

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    page = b.new_page(user_agent=UA)
    resp_urls = []
    page.on("response", lambda r: resp_urls.append(r.url) if "json" in (r.headers.get("content-type") or "") else None)
    page.goto(URL, wait_until="domcontentloaded", timeout=30000)
    page.wait_for_selector("[class*=item]", timeout=10000)   # 或 wait_for_response
    # 拿到接口清单后：优先 page.evaluate 调 fetch 复用会话翻页，见 §3.3
```

## §3 滚动加载与虚拟列表

### 3.1 先拦接口（八成能拦到）

滚动加载站几乎都有 XHR 分页接口。开页面后滚两屏，`resp_urls` 里多出来的 JSON 请求就是真分页接口 → 回 接口优先法 §3。**拦到就离开本节。**

### 3.2 拦不到才模拟滚动

```python
prev, stall = 0, 0
while stall < 3:                                   # 连续 3 轮不增长即到底
    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    page.wait_for_timeout(2000)
    cur = page.locator("[class*=item]").count()
    if cur == prev: stall += 1
    else: stall, prev = 0, cur
    if cur >= 2000: break                          # 上限保险丝
items = page.locator("[class*=item]").all_inner_texts()
```

### 3.3 虚拟列表（DOM 只保留可见几十条）

特征：滚到底 `count()` 不涨但接口请求在涨——DOM 复用节点，滚屏拿不到全量。对策二选一：

1. **改抓接口**（正路）：滚动触发的 XHR 就是分页接口，直接循环请求（在浏览器会话里最省事）：

```python
rows = []
page.evaluate("window.scrollTo(0, 0)")
while True:
    r = page.evaluate("""async () => {
        const res = await fetch('/api/items?offset=' + arguments[0] + '&limit=20', {credentials:'include'});
        return await res.json(); }""", len(rows))
    batch = r["data"]["list"]
    if not batch: break
    rows.extend(batch)
    page.wait_for_timeout(random.randint(1500, 3000))
```

2. 抓不到接口（纯前端本地截断）：认输，说明该数据不适合滚动采集，台账记录原因。

## §4 反爬工程应对

### 4.1 请求更像浏览器（按序排查，改一项测一次）

| 手段 | 做法 | 说明 |
|------|------|------|
| UA 一致 | 全程固定一个真实 Chrome UA（SKILL.md 纪律 4） | 别轮换，会话指纹反而不连贯 |
| Referer 带 path | `"Referer": "https://example.com/list?page=2"` | 空 Referer 的 API 请求最显眼；图片/附件下载尤其查 Referer |
| Cookie 链 | 先 `s.get(BASE)` 收 Set-Cookie，再带 Cookie 请求接口（requests.Session 自动） | 很多 403 只是缺首访 Cookie |
| Accept 全套 | `Accept/Accept-Language/Accept-Encoding` 与真实浏览器一致 | 从 copy-as-curl 抄 |
| 头顺序 | python dict 保序，按浏览器真实顺序插入 headers | 仅极端指纹站才校验，一般不用管 |

### 4.2 Cloudflare 5s 盾判定与放弃

```bash
curl -s -o /tmp/r.html -D /tmp/h.txt https://example.com/
rg -i 'cloudflare|cf-mitigated|challenge-platform|Just a moment' /tmp/h.txt /tmp/r.html
```

命中即盾。处置：`playwright` 真浏览器开一次常能自然过（等 `page.wait_for_selector("body", state="visible")` 后查标题不是 "Just a moment"）；**同一任务重试 2 次仍盾 → 放弃，台账记「CF 盾」，换目标面**。不上代理池、不上盾破解服务。

### 4.3 明确停止信号（见到即停，不算失败）

| 信号 | 处置 |
|------|------|
| 验证码（图片/滑块/点选） | 停止整个任务，台账记「验证码」，告知用户 |
| 登录墙/跳转 login | 数据非公开 → 合规红线，停 |
| 接口返回「请求过于频繁/风控拦截」文案 | 降速一档（间隔 ×3）再试 1 次，仍拦即停 |
| 封 IP（全部请求同错） | 停，不改 IP 硬冲 |

## §5 去重与增量

### 5.1 三层去重

| 层 | 键 | 实现 |
|----|----|------|
| URL 层 | sha16(url) | 采前查 state.json 的 done_urls，命中跳过 |
| 记录层 | 业务主键（id） | `dict` 按 id 覆盖，最后统一写 |
| 内容层 | sha256(规范化文本) | 见 5.2，判断「同 id 内容变没变」 |

### 5.2 content hash 与条件请求（周期重采只要变更）

```python
import hashlib
def chash(item):                       # 规范化：剔除时间戳类易变字段后哈希
    stable = {k: v for k, v in item.items() if k not in ("crawl_time", "updated_at_human")}
    return hashlib.sha256(json.dumps(stable, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:16]

# HTTP 层优先用条件请求，304 直接跳过，省流量
etag = last_etag.get(url)
h = {"If-None-Match": etag} if etag else {"If-Modified-Since": last_lm.get(url, "")}
r = s.get(url, headers=h, timeout=15)
if r.status_code == 304: mark_unchanged(url); continue
if r.headers.get("ETag"):  last_etag[url] = r.headers["ETag"]
if r.headers.get("Last-Modified"): last_lm[url] = r.headers["Last-Modified"]

# 应用层：content hash 与旧值比对
if old_hash.get(item["id"]) == chash(item): continue    # 没变不写
append_jsonl("items.jsonl", item)                        # 变了才落盘
```

### 5.3 增量策略选择

| 需求 | 策略 |
|------|------|
| 只补新记录 | 按 id/时间倒序翻页，撞到 done 集合里的 id 即停（接口支持 sort 时最优） |
| 检测字段变更 | 全量翻列表拿轻字段 → 对变更候选（updated_at 新的）抓详情比对 content hash |
| 每日快照 | 全量重跑 + 当日文件名 `items-2026-10-10.jsonl`，靠 URL 层去重防重复采 |

## §6 失败分类表（先归因，再动作）

| 现象 | 先判 | 处置 | 放弃阈值 |
|------|------|------|---------|
| 超时/连接重置 | 换 1 个 URL 测是否全网慢 | 重试 ≤3 次指数退避 2s→8s→30s | 3 次后跳过该条，记台账 |
| 403 | §4.1 补 Referer/Cookie 链再试 | 修复 1 次；仍 403 → 查 §4.2 是否盾 | 修 2 轮仍 403 → 停该域 |
| 429 | 读 `Retry-After` 头（秒） | 按头等待（无头则 60s）；全局间隔 ×3 降速 | 降速后仍连续 429 → 停 |
| 内容为空（200 但无数据） | 判原因：渲染未完成？参数错？风控假响应？ | ①加等待重试 1 次 ②对照浏览器响应找参数差异 ③响应体含「频繁/拦截」→ 按 4.3 停 | 3 种各试 1 次仍空 → 跳过 |
| 5xx | 是否伴随其他域正常 | 退避重试 ≤3 次 | 3 次后跳过 |
| 302 跳登录 | 目标数据非公开 | 立即停（合规红线） | — |

熔断纪律：**连续 5 次失败（不管哪类）暂停整个任务**，落盘断点后退出，台账写清最后一类失败现象。禁止对同一 host 无间隔硬重试。
