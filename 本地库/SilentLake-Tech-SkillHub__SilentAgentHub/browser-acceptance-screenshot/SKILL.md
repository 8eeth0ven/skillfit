---
name: browser-acceptance-screenshot
description: Validate a real web user journey and capture reviewable screenshot evidence. Use for frontend changes, live sites, authenticated flows, visual regressions, browser console failures, or acceptance that cannot be proven from source alone.
---

# Browser Acceptance Screenshot

1. Derive the exact user journey and expected result from the approved Plan and acceptance criteria.
2. Choose the browser surface: connected Chrome for existing login state, in-app Browser for isolated navigation, or project browser automation for repeatable local tests.
3. Record environment, URL, viewport, account role without credentials, and data preconditions.
4. Execute the critical path plus the highest-risk error, empty, permission, and recovery states.
5. Inspect console errors, network failures, broken links, layout overflow, keyboard access, and loading states.
6. Capture screenshots at decision points, name them with task, step, and timestamp, and link them from `流程管理/验收清单.md`.
7. Log failures in problem and debug records; never crop evidence so tightly that location and state cannot be identified.

A screenshot proves only the observed state. Pair it with interaction and console evidence when claiming functional acceptance.
