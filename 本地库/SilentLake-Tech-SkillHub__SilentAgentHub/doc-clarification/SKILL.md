---
name: doc-clarification
description: Control 产品管理/clarification.md as the governed requirement-intake ledger. Use for every new or materially changed user request and when project-initialization creates or audits the intake record.
---

# Clarification Ledger Controller

This Skill exclusively controls `产品管理/clarification.md`. Semantic clarification is performed by `requirement-clarification`; this document preserves human-readable lifecycle evidence.

## Required entry

Append one entry per requirement intake or material clarification:

- timestamp and stable requirement ID;
- user request or faithful summary plus source links;
- current status and target stage;
- Skills/plugins called and why;
- assumptions, questions, and clarification result;
- classification, complexity, affected modules, risks, and acceptance direction;
- output routes to the requirement pool, Decision, Plan, research, or task;
- latest result and next action.

## Governance

- Preserve chronological history; never rewrite the user's original intent silently.
- The controlling Skill validates fields and status. Markdown records the event and outcome; it does not define transition logic.
- Update `ROUTER.md` through `doc-router` only when this file is created, moved, renamed, or retired.
- Link to downstream records by stable IDs and avoid duplicating their full content.

