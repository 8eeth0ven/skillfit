---
name: doc-design
description: Control 产品管理/Design.md. Use when 涉及页面、交互、视觉、体验或业务流程设计，or when project-initialization creates or audits this artifact.
---

# 产品与交互设计规范 Controller

This Skill exclusively controls `产品管理/Design.md`. It creates, validates, and updates this artifact without taking over the semantic work of requirement analysis, planning, decision-making, engineering, or approval.

## Trigger

- 涉及页面、交互、视觉、体验或业务流程设计。
- `project-initialization` selects this controller from `.codex/harness/document-controllers.json` when the artifact is required for the project type or enabled module.

## Contract

- Purpose: 维护设计目标、用户流程、界面状态、交互规则、素材、可访问性和设计验收证据。
- Use `assets/template.md` as the initial structure; preserve newer user content and append the smallest valid delta.
- Validate the required headings, stable identifiers, links to related records, and current status before returning.
- Update `ROUTER.md` through `doc-router` only when this file is created, moved, renamed, or retired.
- Never duplicate another artifact's facts. Link by requirement, task, decision, issue, version, or release ID.
- Runtime Skill/Hook events belong in `.codex/harness/runtime-events.jsonl`, not this Markdown file.

## Boundaries

- Keep this Markdown artifact as human-readable governance evidence. Its controller or semantic Skill owns validation and transitions; the file records timestamp, triggering user request, called Skills/plugins, current status, related IDs, result, and next route.
- Do not create a Markdown state-machine definition. Raw Hook/Skill telemetry remains in the machine event log; this artifact keeps only calls needed to explain its own lifecycle.
- Do not approve a Plan, decision, release, or acceptance on the user's behalf.
- If a required field is unknown, mark it explicitly and route the gap to the responsible semantic Skill.
