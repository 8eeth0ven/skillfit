---
name: decision-ledger
description: Record a material product, architecture, scope, process, or operational decision with alternatives, tradeoffs, approval, and downstream effects. Use whenever multiple viable choices exist or a user review changes the selected direction.
---

# Decision Ledger

## Decision record

Write to `流程管理/决策记录.md`:

- decision ID, time, owner, status, and linked task or Plan;
- background, question, constraints, and evidence;
- candidate options and comparison across user effect, effort, risk, reversibility, maintenance, and compatibility;
- recommended option and explicit reason;
- user review result and exact approved scope;
- affected requirements, modules, records, validation, rollout, and rollback;
- superseded decision and version when applicable.

Use `待审批`, `已批准`, `已拒绝`, `已替代`, or `已撤销`. Engineering may not treat `待审批` as authorization. Update the Plan Decision Log and all dependent records after approval.
