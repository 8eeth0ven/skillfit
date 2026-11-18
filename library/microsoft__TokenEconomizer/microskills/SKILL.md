---
name: "microskills"
description: >
  Show the repository facts (micro-skills) TokenEconomizer learned and injects at the start of each session here, and the ones still forming. Use when the user asks what TokenEconomizer learned or injects, or about its facts or micro-skills.
---

# TokenEconomizer: microskills

Run this command in the repository's root directory:

```
"${TOKENECONOMIZER_HOME:-$HOME/.tokeneconomizer}/bin/te" --host codex --cwd "$(pwd)" microskills
```

Show the output verbatim in a code block, with no commentary.

The command reads and writes only TokenEconomizer's own state (under `~/.tokeneconomizer`); it
makes no model call. If it reports that the launcher does not exist, the plugin has not run in a session yet:
ask the user to start a new Codex session in this repository first.
