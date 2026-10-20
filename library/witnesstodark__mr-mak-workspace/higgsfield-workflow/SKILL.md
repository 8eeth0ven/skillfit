---
name: higgsfield-workflow
description: Use the official Higgsfield CLI or its Blender integration to discover models, generate requested assets and resume recorded jobs.
---

# Higgsfield operations

Install the official CLI and vendor skills from their maintained sources. Use
the recipient's own account. The CLI and a Blender-native integration have
different execution contexts; preserve the working route selected by the task.

Read-only discovery:

```text
higgsfield --version
higgsfield model list --json
higgsfield model get <job-type> --json
higgsfield workflow list --json
higgsfield generate get <job-id> --json
```

Inspect the exact model's input/media schema before creating a job. A display
name, fal endpoint and Higgsfield job type are different identifiers. Model IDs
and supported flags can change; use the current CLI help and catalog. Do not
replace the user's chosen provider or model with a skill's historical default.

For a requested generation, use the current `generate create` syntax, with the
chosen job type and required inputs. Save the returned job ID immediately.
Resume a slow job using `generate get` or `generate wait`; a waiting timeout
does not justify submitting it again. Inspect a terminal error before retrying.
Keep estimated credits separate from observed billing.

Download outputs and inspect them. For Blender integration, verify that the
asset was imported and the scene saved, not merely that the remote job finished.
Do not replay numbered project scripts that can submit jobs or depend on old
checkpoints. They are not necessarily safe to run twice.

Example: request one prop from a supplied reference, save its job ID, download
the model and verify materials in a disposable Blender scene. Do not claim a
rigged or game-ready result from successful mesh generation alone.

Dependencies: [official CLI](https://github.com/higgsfield-ai/cli),
[vendor skills](https://github.com/higgsfield-ai/skills), an account, and the
Blender companion only when that route is used. Vendor tools are not copied here.
