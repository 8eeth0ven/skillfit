# 明细目录（总索引）

> 用法：先在这里定位"管什么"，再开命中文件的命中节；禁止通读整库。

| 文件 | 管什么 | 何时开 |
|---|---|---|
| audit-workflow.md | 六步流程、污点链判定、可达性/过滤强度口径、报告两张表与分级 | 刚拿到代码库；找到疑似 sink 要定性；要出报告 |
| sinks-java.md | Java 生态污点源与危险汇（SQL/SpEL/OGNL/反序列化/XXE/SSTI/命令执行/权限注解/JWT）+ CVE 模式 | 目标是 JVM 系语言/框架 |
| sinks-php.md | PHP 原生危险函数 + Laravel/ThinkPHP/WordPress 特有面 + POP 链起点 + CVE 模式 | 目标是 PHP 系 |
| sinks-python.md | Python 污点与 SSTI/pickle/yaml 反序列化 + Django/Flask/FastAPI 特有面 + CVE 模式 | 目标是 Python 系 |
| sinks-go-node.md | Go 与 Node.js 双章：SQL 拼接/命令注入/SSRF/路径穿越/原型污染/text-template + CVE 模式 | 目标是 Go 或 Node 系 |

## 开节速查（grep 法）

```bash
grep -n "§" kb/audit-workflow.md        # 六步流程节号
grep -n "^## " kb/sink速查-*.md         # 各表漏洞类节名
```

## 组合拳提示

- 审 web 项目：`审计流程§1 地图` → 对应栈速查表全节 → 回 `§3 污点链判定` → `§5 报告`
- 审依赖库：直接开对应栈速查表的 `历史 CVE 模式` 节反查特征
- 只出加固建议不出漏洞：`§5 报告` 的复现表换 remediation 视角填
