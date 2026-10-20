---
name: secure-code-audit
description: 白盒源码安全审计：从入口到利用链到报告的全流程。多栈 sink 速查（Java/PHP/Python/Go/Node）、污点链追踪、鉴权矩阵、历史 CVE 模式匹配。当用户提到：代码审计、白盒审计、安全审计、审代码、审计这个项目、找漏洞（有源码）、漏洞挖掘（源码）、source/sink、污点分析、反序列化审计、SQL 注入审计 等时触发。
---

# 白盒源码安全审计（secure-code-audit）

**一句话定位**：拿到源码 → 六步走完 → 输出可复现的漏洞报告；表格优先、按需开节、不空扫不误报。

## 必读短表

| 场景 | 先做什么 | 开哪节 |
|---|---|---|
| 刚拿到代码库 | 定栈定框架定入口，§1 三分钟画地图 | 知识库/审计流程与报告.md |
| Java / Spring 系 | 按 SQL/SpEL/反序列化/XXE 逐类过 sink | 知识库/sink速查-Java.md |
| PHP / Laravel / ThinkPHP / WP | 先查注入与反序列化 POP 链起点 | 知识库/sink速查-PHP.md |
| Python / Django / Flask / FastAPI | SSTI 与 pickle/yaml 双重点 | 知识库/sink速查-Python.md |
| Go / Node.js | text/template 与原型污染双重点 | 知识库/sink速查-Go-Node.md |
| 找到疑似 sink | 回溯污点源，确认可达性与过滤强度 | 知识库/审计流程与报告.md §3 |
| 要出报告 | 两张表格式 + 分级口径 | 知识库/审计流程与报告.md §5 |
| 只想先跑自动化 | 每张 sink 表末节有 semgrep/codeql 查询思路 | 对应速查表 §自动化辅助 |

## 执行纪律

1. **先地图后深挖**：入口（路由/Controller/命令行）→ 中间件链 → 数据层，画完对象图再挑肥面
2. **污点链完整才算数**：source → 传播 → sink 三段都落在纸上，断链即标记"疑似"不进报告
3. **过滤要证伪不要默认**：每个过滤点先找黑名单缺口/编码差异/二次解码，证伪后才降级
4. **同对象先升链**：同一参数位置既有低危又有高危，只报高危链，低危作链上节点
5. **鉴权面优先于注入面**：越权是业务逻辑里的静默炸弹，sink 表之外的独立检查项
6. **不堆低危**：信息泄露类合并一条报，不刷条数
7. **授权边界**：只审用户拥有/授权的代码；依赖漏洞给 CVE 编号与修复版本即可

## 产物约定

```
<任务目录>/
├── 对象图.md      # 入口-中间件-数据层 地图（§1 产物）
├── 漏洞清单.md    # 两张表：漏洞总表 + 复现明细表（§5 模板）
└── 线索.md        # 疑似断链/待深挖，逐条追加
```

## 目录

- 知识库/明细目录.md — 总索引：每文件管什么、何时开
- 知识库/审计流程与报告.md — 六步流程 + 污点链判定 + 报告两张表
- 知识库/sink速查-Java.md — Spring/Mybatis/Fastjson/Shiro 全家
- 知识库/sink速查-PHP.md — 原生函数 + Laravel/ThinkPHP/WordPress
- 知识库/sink速查-Python.md — Django/Flask/FastAPI + pickle/yaml
- 知识库/sink速查-Go-Node.md — gin/gorm + express/原型污染
