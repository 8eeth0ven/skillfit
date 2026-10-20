---
name: code-review-closeout
description: Review a completed change for correctness, regressions, security, maintainability, user impact, validation gaps, and workflow-record consistency. Use before acceptance, commit, release, handoff, or when addressing review comments.
---

# Code Review Closeout

1. Re-read the approved scope, changed files, user-owned changes, module boundaries, and acceptance criteria.
2. Review behavior and data flow before style. Look for incorrect assumptions, edge cases, error handling, concurrency, compatibility, migration, security, privacy, permissions, and rollback gaps.
3. Check tests and validation against the actual change; identify untested behavior and misleading success claims.
4. Verify documentation, Router, Plan, task, issue, risk, acceptance, and version records match the implementation.
5. Rank findings by impact and attach each to the tightest file or behavior location. Separate blocking defects from suggestions.
6. Re-run relevant checks after fixes and close comments only with evidence.

If no actionable finding remains, state residual risks and unverified areas; do not manufacture findings or claim full correctness beyond the evidence.
