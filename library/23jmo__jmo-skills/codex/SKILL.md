---
name: codex
description: Hand off a scoped implementation, code review, or technical second opinion to the OpenAI Codex CLI from Claude Code. Use when the user asks to delegate work to Codex or get an independent review.
disable-model-invocation: true
---

# Codex handoff

This is JMO's standalone handoff skill. It is not gstack's `/codex` skill and does not require gstack.

## Prepare the task

1. Check `command -v codex` and `codex exec --help`. If missing, direct the user to https://developers.openai.com/codex/cli/ and explain that they must install and sign in to Codex. Do not claim a handoff ran when the CLI is unavailable.
2. Read the repository instructions and inspect `git status --short`. Identify the working directory, requested mode (review, advice, or implementation), allowed files, and acceptance criteria. Default to read-only review when the request does not authorize edits.
3. Write a focused prompt containing the user's task, relevant paths, constraints, and required checks. Include enough context for a separate agent without passing credentials or unrelated private material. Tell Codex which files are already modified and to preserve those changes.

## Run Codex

Use the user's configured model. Pass the prompt through stdin or a quoted heredoc, not interpolated shell text. Replace the example directory with the actual absolute project path:

```sh
codex exec --sandbox read-only --cd '/absolute/project/path' - <<'TASK'
Review the specified changes. Do not edit files. Report actionable findings with file locations, evidence, and uncertainty. Follow the repository's instructions.
TASK
```

For an authorized implementation, use `--sandbox workspace-write` and a prompt with the exact task, allowed files, and verification criteria. Do not use flags that bypass approvals or sandboxing. If the task cannot run within the current permissions, report that limitation.

Wait for completion and read the exit status and output. Do not let Claude and Codex edit the same files concurrently. For parallel work, use separate worktrees and explicit file ownership; integrate only after reviewing the resulting changes.

## Verify and report

For a review, inspect the cited code and assess each finding before presenting it as confirmed. For implementation, inspect the diff and run the relevant checks. Report what Codex changed or found, what was verified, and any remaining failures. Do not automatically commit, push, or deploy unless that is part of the user's task.

Task: $ARGUMENTS
