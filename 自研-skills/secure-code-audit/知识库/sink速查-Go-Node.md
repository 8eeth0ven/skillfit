# Go

何时开本章：仓库含 go.mod，入口是 gin/echo/net-http/gRPC handler。主线：污点源 → dao/exec 层 sink 的数据流，ORM 与自拼 SQL 并查。

## 污点源

| 框架 | 污点入口 |
|------|----------|
| gin/echo | c.Query/DefaultQuery/PostForm/Param、c.Bind*/ShouldBind*、c.GetHeader、c.QueryParam(s)/FormValue；c.ClientIP 可伪造勿作鉴权 |
| 原生 net/http | r.URL.Query().Get、r.FormValue/PostFormValue、r.Header.Get、r.MultipartForm.File、r.Body 直读（json/yaml/gob Decode） |
| 二手源 | JWT claims、DB 回读字段、内网回调 body、配置中心值——同污点处理 |

## 危险汇（按漏洞类）

### SQL 注入

| 函数/模式 | 危险条件 | 常见绕过 |
|-----------|----------|----------|
| db.Query/Exec + fmt.Sprintf/`+` 拼接 | 用户输入进 SQL 文本 | `'` 闭合 + `--` 注释、`/* */` |
| gorm Where/Raw/Exec/Order 纯字符串 | Where("a='"+x+"'") 单串条件原样拼接 | 同上；Order/Limit 拼接数字段也中 |
| sqlx.Rebind | 只改占位符样式（? → $1），不是消毒器 | Rebind 之后再拼接照样注入 |

```go
q := fmt.Sprintf("SELECT * FROM u WHERE name='%s'", c.Query("name"))
db.Query(q)                                        // 直接注入
db.Where("name = '" + n + "'").Find(&us)           // gorm 纯字符串条件
db.Raw("SELECT * FROM u WHERE id=" + id).Scan(&u)  // Raw 原样执行
sqlx.Rebind("SELECT ... WHERE id=" + id)           // Rebind 后仍拼接=注入
```

- 安全对照：`Where("name = ?", n)` 才是参数化；`Where(x)` 传单串被当条件原样用；OrderBy/分页字段拼接最易漏——白名单列名，不要转义。

### 命令执行

| 函数 | 危险条件 | 常见绕过 |
|------|----------|----------|
| exec.Command("sh","-c",拼接串) | 整串交给 shell 解释 | `;` `$( )` 反引号 `\n` |
| exec.Command(prog, args...) | argv 含用户输入且目标程序解释 `-` 参数 | `-oProxyCommand`、`--checkpoint`、`--use` |

```go
exec.Command("sh", "-c", "convert "+c.Query("f")) // shell 元字符全生效
exec.Command("git", "clone", repoURL)             // 无 shell 但 argv 可注入 - 选项
// 误区：不走 shell 只免疫引号注入；`-` 开头参数由目标程序（git/ssh/tar）自己解释，仍可注入
```

- 判定顺序：先看是否 `sh -c`（必炸），再看 argv 是否进了解释 `-` 的程序；修复用白名单枚举，不靠过滤元字符。

### SSRF

| 函数 | 危险条件 | 常见绕过 |
|------|----------|----------|
| http.Get/Post/NewRequest + Client.Do | URL 用户可控 | 30x 跳转、DNS rebinding、0x/十进制 IP、0.0.0.0 |
| 自定义 CheckRedirect | 只校验首个 URL | 校验放外面，重定向目标不复查 |

```go
u := c.Query("url")
if !strings.Contains(u, "169.254.") { // 解析前黑名单，先判后解=TOCTOU
    http.Get(u) // 默认跟随 10 次重定向，30x 跳内网元数据
}
```

- 正确姿势：解析出 IP → 私网段全拒 → CheckRedirect 内重复校验 → DialContext 锁 IP 防 rebinding；黑名单必被绕，盯 `Contains(host)` 这类判断。

### 路径穿越

| 函数 | 危险条件 | 常见绕过 |
|------|----------|----------|
| filepath.Join/Clean | 误当白名单；只归约不拦截 | `../../` 归约后逃逸、symlink |
| os.Open/http.ServeFile/embed.FS | 拼接目录+用户输入；embed 编译期快照读不到包外（相对安全） | 绝对路径替换基目录、encoded `../`（解码后未复查）、symlink |

```go
p := filepath.Join("data", c.Query("f")) // f=../../etc/passwd → 逃逸
http.ServeFile(w, r, p)                  // 用 mux 已清洗的 r.URL.Path 相对安全，自定义参数无此待遇
f, _ := os.Open("data/" + c.Query("f"))  // f="/etc/passwd" 直接替换基目录
```

- Clean 是"归一化"不是"防穿越"；正确修法 Resolve 后 `strings.HasPrefix(p, root)` 白名单判定。测试点：`..`、绝对路径、`%2e%2e%2f`（检查在解码前还是后）、symlink。

### SSTI（text/template vs html/template）

| 函数 | 危险条件 | 常见绕过 |
|------|----------|----------|
| text/template Parse(用户串) | 无任何转义 | `{{.Secret}}` 遍历字段、调导出方法 |
| html/template + template.HTML 强转 | 跳过上下文转义 | 直接渲染用户 HTML/XSS |

```go
t, _ := template.New("x").Parse(userStr) // text/template：无转义，{{.}} 遍历字段/调导出方法
t.Execute(w, data)
// html/template 唯一的免转义通道是类型强转：
tpl.Execute(w, map[string]any{"h": template.HTML(c.PostForm("h"))}) // 强转=直接 XSS 面
```

- text/template 永不用于渲染用户模板；html/template 的免死金牌只有 `template.HTML` 类型转换——全局搜这个转换即定位 XSS 面。

### 反序列化

| 函数 | 危险条件 | 常见绕过 |
|------|----------|----------|
| gob.Decode 到 interface{} | gob.Register 注册面过宽 | 实例化任意已注册类型 |
| json/yaml Unmarshal 到 struct | 敏感字段（Role/Token/Path）被请求体覆盖 | 冗余字段/键注入 |

```go
gob.Register(map[string]any{})             // 注册越多可用类型越多
var v any; gob.NewDecoder(r.Body).Decode(&v)
json.Unmarshal(body, &cfg)                 // 字段覆盖型"反序列化漏洞"最常见
```

- Go 无 Java 式 gadget 链，主战场是**字段覆盖**：BindJSON 直接打满结构体、`roles` `isAdmin` 字段可被客户端写。
- yaml.Unmarshal 用户输入到 interface 再断言，注意 map 键注入下游拼 SQL/路径。

### JWT

| 函数 | 危险条件 | 常见绕过 |
|------|----------|----------|
| jwt.Parse 无 ValidMethods | 算法未白名单 | RS256 票据改 alg=HS256，公钥当 HMAC 密钥重签 |

```go
jwt.Parse(tok, func(t *jwt.Token) (any, error) { return pub, nil })
// 缺 WithValidMethods([]string{"RS256"}) → RS256 票据改 HS256、公钥当 HMAC 密钥重签即过
```

- dgrijalva/jwt-go 已停维（含 CVE），升级 golang-jwt/jwt/v5 并显式白名单算法；手工断言 MapClaims 验 exp/aud 的逐个核缺省值。

## 历史 CVE 模式

| 编号 | 根因 | 查找特征 |
|------|------|----------|
| CVE-2020-26160 | dgrijalva/jwt-go 未强制校验 aud，Parse 后自断言绕过 | jwt.Parse + MapClaims 手工断言且无 aud 白名单 |
| CVE-2018-16873 | go get 恶意模块 URL 未过滤，元字符注入执行 git 子命令 | exec + Sprintf(仓库 URL) |
| CVE-2021-3121 | gogo/protobuf 生成代码 Unmarshal 缺长度校验，越界读写 | 自动生成 *.pb.go 的 unmarshal 循环 |
| CVE-2021-38561 | yaml.v3 超长文档解析越界读/panic | yaml.Unmarshal 用户 YAML |

## 自动化辅助

1. gosec 全量：G201/G202（SQL 格式化/拼接）、G204（变量起子进程）、G304（变量路径）、G107（可控 URL）；无跨函数污点分析，命中后回溯来源剔除常量误报。
2. govulncheck 按调用图确认依赖 CVE 真实可达，优先于 go.sum 纯版本比对。
3. semgrep 自定义规则：gorm `Raw/Exec` 参数为表达式、`sqlx.Rebind` 后接拼接、`jwt.Parse` 缺 `ValidMethods`（查属性缺失，比字符串匹配准）。

# Node.js

何时开本章：package.json 含 express/koa/fastify/graphql 及 db/orm 驱动。主线：路由/中间件 → db、child_process、fetch、模板渲染的数据流；原型污染当独立链查。

## 污点源

| 框架 | 污点入口 |
|------|----------|
| Express | req.query/body/params/headers/cookies、multer 的 req.file(s)（originalname/path 用户可控） |
| Koa/Fastify | ctx.query/body/params、request.query/body/params |
| GraphQL | 每个 resolver 的 args/source——全部按污点处理，别只看入口层 |
| 二手源 | proxy 转发头、JWT claims、模板 options、Object.assign 出来的"配置" |

## 危险汇（按漏洞类）

### SQL 注入

| 函数 | 危险条件 | 常见绕过 |
|------|----------|----------|
| mysql/mysql2 `.query(拼接串)` | 模板字符串/`+` 进 SQL | `` `...${id}` ``、`'` 闭合 |
| sequelize/knex 原始接口 | whereRaw/literal/query 原样拼 | 参数化层被 literal 绕过 |
| Mongo findOne/find | 查询对象直接吃 body | 操作符注入 `{"$gt":""}`、`$where`、`$ne` |

```js
db.query(`SELECT * FROM u WHERE id=${req.query.id}`) // 模板字符串=拼接
knex('u').whereRaw('n=' + n)                         // 原样拼；sequelize.literal 同理
// Mongo 操作符注入：body 传 {"user":{"$gt":""},"pass":{"$gt":""}} 无条件命中第一条
User.findOne({ user: req.body.user, pass: req.body.pass })
```

- mysql2 `execute()` 走 prepared 才参数化，`query()` 传数组只是客户端转义；Mongo 面治本用 mongoose `sanitizeFilter` / express-mongo-sanitize，不靠黑名单键。

### 命令执行

| 函数 | 危险条件 | 常见绕过 |
|------|----------|----------|
| child_process.exec/execSync | 默认 `/bin/sh -c` | `;` `$( )` 反引号换行 |
| execFile/spawn | 目标程序解释 `-` 参数或 `shell:true` | argv 注入 `-` 选项 |
| eval / new Function / vm | 输入即代码 | vm 不是安全边界（历史多次逃逸） |

```js
exec(`convert ${req.query.f}`)   // sh -c，元字符全生效
execFile('convert', [f])         // 无 shell；目标解释 - 时仍可注入
eval(s); new Function(s); require(p) // 任意 JS；动态 require/import 可控路径=执行任意模块
```

- 修复：execFile + 值白名单 + 拒绝 `shell:true`；eval/new Function 没有安全用法只能删除；`NODE_OPTIONS`/`--inspect` 出现在日志回显里是 RCE 后利用面。

### SSRF

| 函数 | 危险条件 | 常见绕过 |
|------|----------|----------|
| axios/got/fetch(url) | URL 用户可控 | 30x 跳转、rebinding、元数据地址 |
| request（存量废弃包） | 默认跟随且允许 file 等协议 | 协议切换 file:// |

```js
const u = new URL(req.query.url)
if (!/internal/.test(u.hostname)) await axios.get(u.href) // 只查字符串不查解析后 IP
// 跳板：169.254.169.254（阿里云 100.100.100.200）、0x7f000001、0.0.0.0、[::1]
```

- 校验必须在"解析出 IP 之后、发请求之前"做且 maxRedirects 每跳复查（axios 默认 follow 5 次）；拿到 SSRF 先打云元数据取临时凭证。

### 路径穿越 + 原型污染 → RCE 链

| 函数 | 危险条件 | 常见绕过 |
|------|----------|----------|
| path.join(root, u) / path.resolve(u) | join 只 normalize 不拦 `../`；resolve 绝对段丢 base | `../` 逃逸、`/etc/passwd` |
| res.sendFile(p, {root}) | p 为绝对路径时忽略 root；自拼 join 无检查 | encoded `%2e%2e%2f`（Express 已解码后再检查才有效） |
| lodash merge/set/defaultsDeep | 用户 JSON 含 `__proto__`/`constructor.prototype` 键 | 污染 Object.prototype → 控制下游选项 |

```js
path.join(root, req.query.f)       // ../ 仍可逃逸
path.resolve(req.query.f)          // 绝对路径丢弃 base
res.sendFile(req.query.f)          // 未限 root 且 f 绝对 → 任意读
_.merge({}, JSON.parse(body))      // __proto__ 落地污染 → outputFunctionName → ejs RCE
```

- JSON.parse 的 `"__proto__"` 只是自有属性不落地，**落地发生在深合并/assign/setPrototypeOf**——审 merge 出现点，不是 JSON.parse 点。
- express.static 内建防穿越；自写中间件 + `join(root, q)` 没有这层。污染可打的下游：ejs/pug 渲染选项、child_process env/shell、express settings——找到 merge 即追这三个消费方。

### SSTI

| 函数 | 危险条件 | 常见绕过 |
|------|----------|----------|
| ejs.render(用户串) | 模板即 JS | `<% %>` 任意代码 |
| pug.render(用户串) | compile 期执行 | `-` 前缀语句 |
| res.render(固定视图, 选项含用户输入) | 选项被覆盖/被污染 | layout/filename 注入 |

```js
ejs.render(req.body.tpl)                 // 任意 JS
pug.render(req.body.tpl)                 // 编译期执行
res.render('v', { layout: req.query.l }) // 选项混入用户输入，配合原型污染放大
```

- 判定铁律：模板字符串来源必须是代码内常量，用户可影响模板体 = RCE；ejs 选项（outputFunctionName/localName）被合并进 render 参数即高危（CVE-2017-1000228）。

### 反序列化

| 函数 | 危险条件 | 常见绕过 |
|------|----------|----------|
| node-serialize.unserialize（及旧版 funcster/serialize-javascript） | `_$$ND_FUNC$$_` 函数序列化直接还原代码 | IIFE 立即执行 |
| vm2 沙箱跑不可信代码 | 历史多次逃逸 | CVE-2023-37xxx 系列 |

```js
require('node-serialize').unserialize(cookie)
// payload: {"r":"_$$ND_FUNC$$_function (){require('child_process').exec('id')}()"} 尾部 () 即 IIFE 瞬时触发
```

- node-serialize 无安全用法，命中即 RCE；cookie/session 里出现该格式直接出报告。
- 区分层：JSON.parse 无代码执行（污染靠 merge 落地），unserialize 类库有。

### JWT

| 函数 | 危险条件 | 常见绕过 |
|------|----------|----------|
| jwt.decode(token) | 只解不验签，被当鉴权用 | 任意伪造 claims |
| jwt.verify 未显式 algorithms | <9.0.0 校验缺陷面 | alg 混淆/none 残留 |
| verify(t, pub, {algorithms:['HS256']}) | 公钥当 HMAC 密钥 | RS256→HS256 重签 |

```js
jwt.decode(t)                                   // 不验签；当 verify 用=身份伪造
jwt.verify(t, secret)                           // 未传 algorithms：<9.0.0 有混淆/none 残留面
jwt.verify(t, pub, { algorithms: ['HS256'] })   // 公钥当 HMAC 密钥=算法混淆直接通过
```

- 修法：显式 `algorithms:['RS256']` + `issuer/audience` 校验 + 升级 jsonwebtoken ≥9.0.0；全局搜 `jwt.decode` 出现在鉴权中间件的，一抓一个准。

## 历史 CVE 模式

| 编号 | 根因 | 查找特征 |
|------|------|----------|
| CVE-2017-5941 | node-serialize 反序列化函数体即代码 | unserialize(cookie/body) |
| CVE-2019-10744 | lodash merge/set 未拦 `__proto__` 路径 | 深合并用户 JSON |
| CVE-2017-1000228 | ejs outputFunctionName 未过滤拼进 Function 体 | res.render 选项混入用户输入 |
| CVE-2022-23540 | jsonwebtoken <9.0.0 verify 密钥/算法处理缺陷 | verify 未显式 algorithms |

## 自动化辅助

1. npm audit --json + osv-scanner 扫 lockfile 全链路；`npm ls <pkg>` 反查引入路径，重点盯 node-serialize/lodash/ejs/jsonwebtoken 版本。
2. semgrep `p/nodejs` + taint 模式：source 覆盖 req.query/body/params/headers（express/koa/fastify 三套），sink 到 exec/query/whereRaw/sendFile/merge。
3. njsscan 或 CodeQL security-extended 查原型污染与硬编码密钥；所有 merge/extend/defaultsDeep 出现点逐个核 `__proto__`/`constructor` 键过滤。
