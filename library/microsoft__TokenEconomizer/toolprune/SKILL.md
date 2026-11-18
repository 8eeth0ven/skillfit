---
name: "toolprune"
description: >
  Review, undo or apply TokenEconomizer's deny list of Codex capabilities this repository never uses (written to the project's .codex/config.toml). Use when the user asks about TokenEconomizer's tool pruning or deny list, or asks to restore or apply it.
---

# TokenEconomizer: toolprune

Run this command in the repository's root directory:

```
"${TOKENECONOMIZER_HOME:-$HOME/.tokeneconomizer}/bin/te" --host codex --cwd "$(pwd)" toolprune ARGS
```

Use `show` as ARGS unless the user asked to `apply`, `restore` or `measure` (optionally naming capabilities). Never run `apply` or `restore` unless the user asked for it. Show the output verbatim in a code block. If it shows a proposal waiting for `toolprune apply` (under `toolprune=propose`, or one the plugin could not write), end with one line saying how to apply it and that it takes effect from the next session; if it shows a pending list, say that it is written by itself once this repository's sessions have been idle, or now with `apply`.

`apply` and `restore` edit the project's `.codex/config.toml` and record the change in TokenEconomizer's own state under `~/.tokeneconomizer`, outside the workspace, which the sandbox keeps read-only: run that command with `sandbox_permissions` set to `"require_escalated"` and a one-line `justification`, so that Codex asks the user to approve it. `show` and `measure` need no approval.

The command reads and writes only TokenEconomizer's own state (under `~/.tokeneconomizer`)
and, for `toolprune apply` or `restore`, the project's `.codex/config.toml`; it makes no model
call. If it reports that the launcher does not exist, the plugin has not run in a session yet:
ask the user to start a new Codex session in this repository first.
