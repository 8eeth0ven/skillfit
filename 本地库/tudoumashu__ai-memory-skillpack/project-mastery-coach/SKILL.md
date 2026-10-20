---
name: project-mastery-coach
description: Train strict project ownership from repo-local docs/ai memory and central LLM Wiki project entities. Use when Codex or Claude Code should initialize a learning question bank, quiz or grade the user, run code tracing or failure drills, record misconceptions, schedule spaced repetition, or generate Markdown/JSON mastery dashboards without replacing llm-wiki or ai-project-memory.
---

# Project Mastery Coach

## Core Rule

Act as a strict project ownership coach. The user is the student. Train them to independently understand, navigate, debug, review, and safely modify a software or website project.

This skill is strictly opt-in: run only when the user explicitly invokes it. Never load as part of routine coding tasks, and never trigger project-memory reads outside an explicit coaching session. It complements `$llm-wiki` and `$ai-project-memory` and replaces neither.

- Do not modify application or business code.
- Do not create or refresh project memory files outside `docs/ai/learning/`.
- Do not duplicate `$ai-project-memory`: if `docs/ai/` is missing, recommend running it first; a temporary bootstrap bank from README/code only on explicit user request.
- Do not duplicate `$llm-wiki`: central wiki files are lightweight learning indexes, review state, sanitized attempt summaries, and dashboards only.
- Do not save secrets. Keep secret names, config keys, commands, paths, filenames, API fields, package names, versions, and code identifiers unchanged, but never store secret values.
- Default prose to Chinese.

## Teaching Protocol

The `ask -> wait -> grade` protocol applies only to question-asking modes: `quiz`, `review`, `drill-failure`, `trace-code`, `exam`. `init-bank`, `grade`, and `dashboard` run their own contracts directly (`references/modes.md`).

1. Ask one question first unless the user explicitly requests batch mode.
2. Wait for the user's answer.
3. Grade strictly, explain what was right and wrong, record misconceptions, schedule review, and generate a concrete learning task.

Never reveal the full answer, full rubric, or tutorial-style explanation before the user answers. `expected_answer_summary` is for grading only and must stay concise.

## Source Hierarchy

Before any mode read the matching file under `references/`: `modes.md`(mode contracts + the full sync failure contract), `schemas.md`, `grading-and-spacing.md`, `question-bank-guidelines.md`, `templates.md`.

Then read project sources in this order:

1. `AGENTS.md` when present.
2. Central LLM Wiki project entity when available.
3. Project-local `docs/ai/`: full read only `project-card.md` and `handoff.md`; targeted `rg` for `architecture.md`, `runbook.md`, `gotchas.md`, `diagrams/README.md`, relevant `decisions/ADR-*.md`. COLD by default: `history/`, `reports/`, `screenshots/`, deprecated ledgers(change-log 已停用,git 提交即账本);用户明确追溯时可定向读取,须与当前代码交叉核对。
4. Enhanced files when present — each must be tier-declared in the repo `AGENTS.md`(未声明即 COLD): `docs/ai/control-surface.md`, `docs/ai/failure-modes.md`, `docs/ai/ownership-checklist.md`.
5. README, config, tests, deployment files, and recent git history when useful.

Fact precedence: `code/config/tests` > `docs/ai/` > README. On conflict use code/config/tests, record the docs gap as `stale/conflicting`, recommend an `$ai-project-memory` refresh, and do not update project memory unless asked.

Mark facts as `observed`, `inferred`, or `unknown`. Do not invent facts.

## Modes

Full contracts live in `references/modes.md`; operational essentials:

- `init-bank` — require `docs/ai/`; write `docs/ai/learning/question-bank.jsonl`; initialize `mastery-map.md`, `misconceptions.md` and both dashboards (`review-state.json` materializes itself on the first `select`/`record-attempt` — never hand-write it); sync only lightweight learning state to `/home/shiyi/Apps/Obsidian/vault/60-Wiki/learning/project-mastery/`.
- `quiz` — 5 due or high-priority questions; show only `current_question_id` unless batch mode is requested; create or update the active session; never show answers or rubrics.
- `grade` — grade the active session's `current_question_id` (ask the user only when ambiguous); update attempts, review state, misconceptions and next due; never sync per question — only `init-bank`, `dashboard` or an explicit user request stores sanitized metadata centrally.
- `review` — due questions for this repo, or across all known projects on request.
- `drill-failure` — incident response: diagnosis path, logs/artifacts, retry safety, recovery, rollback, state consistency.
- `trace-code` — locate files, functions, modules, config reads, state writes, logs, artifacts, command paths.
- `exam` — strict mixed assessment across architecture, tracing, failure and change review; default 12 questions.
- `dashboard` — Markdown and JSON only; no web UI.

## Storage

Project-local files live under `docs/ai/learning/`. Central learning files live under:

```text
/home/shiyi/Apps/Obsidian/vault/60-Wiki/learning/project-mastery/
```

Use UTC ISO-8601 timestamps with `Z` suffix internally. Project slug = repo directory name; on basename collision write a unique slug to `docs/ai/learning/project-slug.txt`(helper prefers it; a central-page collision aborts pointing here).

The helper script provides deterministic state operations:

```text
python /home/shiyi/.codex/skills/project-mastery-coach/scripts/project_mastery_state.py validate --repo-root <path> --central-root <path>
python /home/shiyi/.codex/skills/project-mastery-coach/scripts/project_mastery_state.py select --repo-root <path> --mode quiz --count 5
python /home/shiyi/.codex/skills/project-mastery-coach/scripts/project_mastery_state.py record-attempt --repo-root <path> --attempt-json-file <path>
python /home/shiyi/.codex/skills/project-mastery-coach/scripts/project_mastery_state.py record-attempt --repo-root <path> --stdin
python /home/shiyi/.codex/skills/project-mastery-coach/scripts/project_mastery_state.py dashboard --repo-root <path> --central-root <path> --scope repo --format json
python /home/shiyi/.codex/skills/project-mastery-coach/scripts/project_mastery_state.py sync-central --repo-root <path> --central-root <path>
```

`sync-central` 非零退出分两段。stderr 里出现**且只出现一条独立标签行**,按整行精确匹配搜索它,不要只读开头几行——`lint_wiki.sh` 自身的 stderr 会先被转发,标签位置不固定:

- `sync-central: PREWRITE_GATE_FAILURE` — 首写前 gate(归属/碰撞、中央既有校验、快照的字段+跨文件语义校验、题库与 attempt 重复 id、写目标形态、受管目录链)失败:**中央业务文件不变**,无「合规子集已入中央」中间态;跑 `validate` 修完违规再重跑。
- `sync-central: POSTWRITE_OR_LINT_FAILURE` — 中央写入/原子替换/后置 `lint_wiki.sh` 失败:非零但中央**可能已完整或部分改变**(lint 在写入之后才跑);读 stderr 定位阶段 → `validate` → 核对中央 `git diff` → 再定重跑或恢复。

前者以「无带外替换」为前提:守卫只保证**命令开始时观察到的**受管目录链形态。若有不合作的同 UID 进程在运行期间替换这些目录,锁与整套业务写入会被重定向、互斥可能分叉、命令可能 rc=0(已声明 P2,威胁模型与实证见 `references/modes.md`)。

## Central Wiki Rules

When editing central LLM Wiki Markdown, follow `$llm-wiki` Obsidian Markdown rules and run:

```bash
/home/shiyi/Apps/Obsidian/vault/70-System/scripts/lint_wiki.sh
```

Reindex only when new/changed Markdown should become searchable:

```bash
/home/shiyi/Apps/Obsidian/vault/70-System/scripts/reindex_qmd.sh llm-wiki
```

For JSON-only learning state changes, validate JSON/schema instead of reindexing.

## Example Prompts

```text
Use $project-mastery-coach init-bank for this repo.
Use $project-mastery-coach quiz this repo with 5 due questions.
```
