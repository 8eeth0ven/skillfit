---
name: feature-handoff
description: Prepare a precise handoff for an agent or developer implementing a feature, continuing a task or reviewing a finished change.
---

# Feature handoff

Read the current project files and relevant terminal or report before writing
a handoff. Use the evidence currently on disk, not an earlier progress message.

Include the intended behavior, affected files, useful starting points, exact
skill paths, known constraints and acceptance checks. For a continuation, add
what is already implemented, what remains, current test results and any running
process that must not be interrupted. Keep secrets and login material out.

Make ownership clear when several agents are working. Identify files that must
not be overwritten. Carry forward accepted choices and unresolved questions.
Do not assign the user work that the receiving agent can complete itself.

Separate the source baseline, selected proposal, implemented behavior, agent
verification and owner acceptance. A selected mockup is not a shipped feature.
For assets, include stable IDs, relevant hashes, local dependency paths and
actual event markers. Name the receiving scene or system, and describe how to
check it at normal gameplay speed. Leave missing values unresolved rather than
turning an example's timing, project names or design taste into requirements.

State who owns shared files and the expected base revision. Re-read shared
state before applying the handoff; reconcile changed inputs instead of
overwriting another agent's work. Keep the current specification current and
put chronological implementation details in a separate log.

For a completed feature, lead with its practical result, then summarize the
change and verification. Link the relevant report or artifacts. Distinguish a
prepared build from an installed update and a submitted job from a reviewed
asset. Read `workspace-authoring` when the handoff is a Workspace deliverable.
