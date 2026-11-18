---
name: "status"
description: >
  Show what TokenEconomizer has learned for this repository, what it has done, and what this repository's sessions cost. Use when the user asks about TokenEconomizer, its status, its savings or overhead, or what it learned here.
---

# TokenEconomizer: status

Run this command in the repository's root directory:

```
"${TOKENECONOMIZER_HOME:-$HOME/.tokeneconomizer}/bin/te" --host codex --cwd "$(pwd)" status
```

Show the output verbatim in a code block. Add nothing unless it contains a warning; then explain the warning in one sentence.

The command reads and writes only TokenEconomizer's own state (under `~/.tokeneconomizer`); it
makes no model call. If it reports that the launcher does not exist, the plugin has not run in a session yet:
ask the user to start a new Codex session in this repository first.
