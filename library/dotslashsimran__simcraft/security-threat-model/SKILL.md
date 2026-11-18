---
name: security-threat-model
description: Threat-model the user's own app from its real code. Draws the data flow (actors, trust boundaries, data stores, external services) as a Mermaid diagram, finds threats per element with STRIDE, ranks them by likelihood times impact, then proves each top risk with a local failing test, fixes it, and keeps the test as a regression test. Covers auth, IDOR and tenant isolation, injection, SSRF, secrets, CORS/CSRF, uploads, webhooks, dependencies, abuse, and LLM-app risks like prompt injection through tool output. Writes THREAT_MODEL.md. Use when the user says "threat model", "security review of my app", "is this secure", "STRIDE", "find vulnerabilities in my code", or before launching something that holds other people's data or money.
---

# Security threat model

The goal is not a long list of everything that could go wrong. It is the three to six things that would actually hurt, proven real on the user's own machine, fixed, and locked in with tests. A threat without a proof is a guess. A fix without a regression test comes back in six months.

Only for code and systems the user owns. Every proof runs against local code or a local dev server with throwaway data. Never send a proof to production, a staging server shared with others, or any third-party service, even one the app calls.

## 1. Scope (ask, one question at a time)

- What does the app do, who uses it, and what would be bad news (leaked data, lost money, someone else's account, a big bill)?
- What is in scope (which repo, which services) and how does it run locally?
- How is it deployed (behind a proxy, serverless, single box)? This decides which threats are the app's job.

Write the answers at the top of `THREAT_MODEL.md`.

## 2. Map the surface from the code

```
python3 ~/simcraft/skills/coding/security-threat-model/scripts/surface.py <repo>
python3 ~/simcraft/skills/coding/security-threat-model/scripts/secrets_scan.py <repo> --history
```
`surface.py` lists routes with flags (`NO-AUTH-SEEN`, `IDOR?`, `WEBHOOK-UNVERIFIED?`, `ABUSE-TARGET`, `LLM-COST`) and leads grouped by category, with `[input]` on lines that use request data. `secrets_scan.py` finds keys in files and history and prints them masked. Both are regex heuristics: they point at code to read, they never decide anything. Then read by hand, in this order: the auth middleware and how a request becomes a user, the data access layer and how queries are scoped, every route that takes an id, and every place the app calls out (HTTP, shell, files, LLM tools). If there is a lockfile, run `npm audit` or `pip-audit` if installed (see reference).

## 3. Draw the data flow

Write a short `dataflow.yaml` from what the code actually does (actors, processes, stores, externals, boundaries, flows), then:
```
python3 ~/simcraft/skills/coding/security-threat-model/scripts/dataflow.py dataflow.yaml --stride
```
It prints the Mermaid diagram, the flows that cross a trust boundary, and a STRIDE-per-element table to fill in. Every boundary crossing is where threats live. If the diagram has no boundaries, it is wrong.

## 4. Find and rank threats

Go element by element with STRIDE, but spend most of the time on these, because they are where real apps break: authorization (can user A touch user B's or tenant B's object?), injection into SQL, shell, templates and paths, unverified inbound trust (webhooks, JWTs, callbacks), and, for AI apps, what a hijacked model can do with its tools. The reference has what to look for in code for each area.

Rate each threat: likelihood 1 to 3 times impact 1 to 3, with a one-line reason. Anything reachable by any logged-in user or anyone on the internet in one request is likelihood 3. Anything that exposes other customers' data, money or code execution is impact 3. Drop theoretical threats with a one-line reason instead of padding the table.

## 5. Prove, fix, keep the test

For each threat scoring 6 or more (and cheap wins below that):
1. **Prove it.** Write a test that asserts the secure behaviour ("Alice gets 404 for Bob's invoice"), run it, and watch it fail. The failure output is the evidence. Use the app's test framework, or plain HTTP to the local dev server. Add a control test for the normal case so a fix cannot pass by breaking the feature.
2. **Fix it** at the layer where it cannot be forgotten (scope the query by owner, parameterise, resolve and contain the path, verify the signature before parsing). Smallest change that closes the class of bug, not just the payload.
3. **Rerun.** The proof now passes, the controls still pass, and the test stays in the suite.

If a real secret turns up, tell the user to revoke and rotate it at the provider first. Never print it back in full.

## 6. Write THREAT_MODEL.md

Sections: scope, data flow diagram, assets, trust boundaries, threats table (ID, element, STRIDE, threat, L, I, score, status), proofs and fixes (proof, before output, fix), residual risks with the next fix for each, and what to recheck when the system changes. Use the template in `reference.md`.

A complete worked example (an invoice API with an IDOR, SQL injection, path traversal, forged webhook, hardcoded fake key and error leak, plus the fixed copy and 18 tests) is in `examples/invoice-api/`.
