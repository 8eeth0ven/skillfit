---
name: ai-project-memory
description: Maintain bounded, durable AI project memory in a repository's docs/ai/ pack. Use when Codex or Claude Code needs to create, read, update, or audit project memory (project-card, architecture, diagrams, runbook, handoff, gotchas, ADRs), install AGENTS.md memory rules, or sync a lightweight central LLM Wiki project entity for user-owned projects.
---

# AI Project Memory

## Core Rule

每个仓库的 `docs/ai/` 是该项目记忆的唯一事实源;**git 提交是唯一账本**(change-log 类文件已于 2026-07-28 停用,历史封存于 `docs/ai/history/`,不得重建)。

```text
docs/ai/
├── project-card.md      # 卡片:≤60 行,替换
├── architecture.md      # 架构入口:≤250 行,替换/局部更新
├── diagrams/            # README ≤60 行 + *.mmd(一图一文件)
├── runbook.md           # 操作手册:≤150 行,替换/局部更新
├── handoff.md           # 单快照:≤120 行,替换
├── gotchas.md           # 耐久陷阱:≤300 行,追加 + 定期精选
├── decisions/ADR-*.md   # 单篇 ≤80 行,新篇追加,旧篇冷存
└── history/             # 封存区,默认不读
```

记忆散文默认中文;命令、路径、代码标识符、config key、版本号保持英文。不写 secret 值。预算上限见上方结构图;仓库 `AGENTS.md` 只可声明更严(更小)的上限,不得放宽——VERIFY 硬门按固定常量执行,不识别放宽。

## 读取纪律(检索先行)

- **HOT(开机整读,口径 = 字节÷3)**:仓库 `AGENTS.md`、`CLAUDE.md`、`project-card.md`、`handoff.md`——四文件自身目标 ≤7k tokens;四文件 + 当前触发的 skill 正文合计 ≤10k。
- **WARM(按需定向,禁止整读)**:`architecture.md`、`runbook.md`、`gotchas.md`、`diagrams/README.md`、`decisions/`(现行 ADR)——用任务关键词(路径、symbol、config key、报错信息)`rg` 定位小节后只读该节。
- **COLD(默认不读)**:`history/`、`reports/`、`screenshots/`、`learning/`、旧 ADR(Status: superseded/deprecated)。仅任务明确要求追溯时才进,读到的内容必须与当前代码交叉核对后才能引用。
- **非分层新条目**:向 `docs/ai/` 一级新增任何文件/目录,必须同时在仓库 `AGENTS.md` 声明其层级;未声明即 COLD 且属违规(VERIFY 白名单断言会拦)。

## 写入纪律

1. **谁干活谁写**:Codex 与 Claude Code 均可写,完成实质任务的一方负责更新。
2. **强制署名**,actor 只有两个拼法:`claude-code/fable-5`、`codex/gpt-5.6-sol-pro`。
   - `handoff.md` 头部两行,固定列表项形式:`- updated: <ISO8601>`、`- updated_by: <actor>`(守卫与工具用 `grep -m1 '^- updated: '` 读取基线)
   - 追加条目(gotchas / ADR)末行:`— by <actor> · YYYY-MM-DD`
   - git 提交:Co-Authored-By trailer 对应同一 actor
3. **状态用替换**:`handoff.md` 永远是单快照 replace-in-place,不追加历史;追加语义仅限 gotchas 条目与新 ADR。
4. **替换守卫(一体动作)**:写 handoff 前立即重读其头部(`grep -m1 '^- updated: '`,无匹配即中止写入,不得盲写),基线 = 最后一次实际读取的 `updated` 与内容;文件比基线新则先合并再写;临时文件必须建在 `docs/ai/` 同目录(如 `.handoff.md.tmp`——跨文件系统的 `mv` 不原子)再 `mv` 替换;可用 shell 时先解析 repo 根,用绝对路径 `flock <repo根>/docs/ai/.handoff.lock` 包裹「重读-合并-替换」全程,禁止相对路径锁(两个 harness 共用此锁)。守卫作用于**替换既有 handoff**;文件尚不存在的首次创建(初始化新仓或迁移落存根)直接写入含 `- updated:` 头部的完整快照,不适用「无匹配即中止」。
5. **预算写入时执行**:超出上限当场裁剪,不留给下次会话。
6. **git 即账本**:实质任务完成即提交,提交正文写 目标 / 验证 / 风险;禁止积压跨任务未提交改动;不把完整 diff 粘进文档。非 git 仓库(降级安装,收据 `git=no`):提交类条款不适用,改动以文件落盘为准并在最终回复明示「非 git 降级」;不得擅自 `git init`(须用户批准,见 MIGRATE)。
7. **未提交内容不进 canonical 文档**:只可写入 handoff 并标 `WIP/unverified`。非 git 仓库:本条以「未验证」代读「未提交」——未验证内容同样只可写入 handoff 并标 `WIP/unverified`。

## 何时更新什么

实质改动收尾时的最小集合:

- 永远:替换 `handoff.md`(当前目标、已完成、进行中、阻塞、下一步、验证状态、重要 commit)。
- 结构 / 边界 / 部署 / auth / API 变了:`rg` 定位后更新 `architecture.md` 相应小节与相关 `.mmd`。
- 命令 / env / 迁移 / 部署方式变了:更新 `runbook.md` 相应小节。
- 踩到耐久新坑:向 `gotchas.md` 追加一条(带署名尾行);发现旧条目失效顺手删除。
- 长期架构决策:新增 `decisions/ADR-xxxx.md`(Context / Decision / Consequences / Status)。
- 纯小改:只替换 handoff,并在最终回复说明其他文件无需更新。

## 初始化(新仓库或老仓库补记忆)

1. 只做文档与记忆初始化,不改业务代码。
2. 依据:README、包与运行时 manifests、框架/路由/数据库/部署/CI 配置、`rg --files` 源树、`git log --oneline -n 30`(非 git 仓库跳过)。
3. 按上方结构与预算生成 `docs/ai/`;拿不准的写 `inferred` 或 `unknown`,禁止编造业务意图、外部服务、凭证。
4. 用户要求安装持续规则时,在仓库 `AGENTS.md` 增补 Project Memory 节(≤40 行):HOT/WARM/COLD 文件清单、写入纪律(引用本 skill)、仓库特有实例事实(预算仅可收紧,见核心规则)。保留既有无关规则,合并不删除。
5. 用户拥有的项目:创建或更新中央 wiki 轻量 project entity(见下节)。

## 中央 LLM Wiki 同步(低频)

仅当 **entity 级事实**变化(项目新建/归档、架构方向调整、路径或 remote 变更)时,更新中央 project entity。**定位先于命名(fail-closed)**:先 `rg -lF "<repo根>" /home/shiyi/Apps/Obsidian/vault/60-Wiki/entities/` 反查,再逐个命中页核对归属,判据唯一——**页 frontmatter 的 `source_paths` 含本仓根**才算本仓页,正文提及本仓路径不算(他项目页常引用本仓路径)。恰一页合判据:更新该页(既有页名未必是仓库名的机械变形),禁止另建同仓新页;多页合判据:停止写入并报告用户裁定(同仓多页属待合并异常);命中页全不合判据即视同查无。查无且触发器是路径变更时,先用旧根按同判据再查一遍(命中即更新该页,并把 `source_paths` 刷新为新根);旧根不可得则在同一 entities/ 目录 `rg -ilF "<项目名>"` 找候选,归属仍不可判即停止并报告。查无(路径变更场景须两路都查无)才以唯一 slug 新建 `entities/<repo-slug>.md`;任何情况下不覆盖他仓页。页面内容:repo 路径、`docs/ai/` 路径、关键文件链接、简短摘要、重要 gap。不逐任务同步,不复制完整项目文档进中央。编辑遵循 `$llm-wiki` 规则(frontmatter 写 `updated_by: <actor>`),改后运行 `lint_wiki.sh`;内容变更才运行 `reindex_qmd.sh llm-wiki`。

## 收尾自检与最终回复

- 自检:写入是否全部带署名、守预算?handoff 是否仍为单快照?是否有该提交而未提交的改动?(非 git 仓库:此问不适用,改核对最终回复已明示「非 git 降级」)
- 最终回复列出:改了哪些 `docs/ai/` 文件、跑了什么验证、是否同步中央 entity、遗留 gap 或风险。
