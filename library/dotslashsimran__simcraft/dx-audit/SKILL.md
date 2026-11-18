---
name: dx-audit
description: Audit the developer experience of a developer tool (SDK, API, CLI, framework) by trying it exactly like a brand-new developer, from the official docs only, in a fresh empty environment. Logs every step with timestamps and friction tags, measures time to first success, steps, page switches, errors and lines of code, finds where people would give up, grades three error messages, and writes a fair teardown with the top 5 fixes as ready-to-paste doc and error rewrites. Use when the user says "audit the developer experience of X", "DX teardown", "DX audit", "try this SDK like a new user", "onboarding friction", "time to first success", "how good are X's docs", or wants a teardown to send to a company's DevRel team.
---

# DX audit

You play a competent developer who has never seen this tool. You follow the official docs literally, write down everything that happens, and turn it into a teardown the company's DevRel team would want to read. The output is evidence, not opinion: every complaint has a timestamp, a URL, the exact output, and a fix.

Scripts (Python is standard library only, Node uses the repo's `playwright`):
```
python3 ~/simcraft/skills/coding/dx-audit/scripts/friction.py   # written "friction.py" below
node ~/simcraft/skills/coding/dx-audit/scripts/snapshot.mjs      # written "snapshot.mjs" below
```
If `playwright` does not resolve, run `npm install` in `~/simcraft` once. Read `reference.md` for the tag definitions, grading rubric, time model and a worked example.

## 1. Set up (ask the user, one question at a time)

1. **The tool and ONE goal.** A real first task, such as "send my first traced LLM call", "deploy hello world", "create a project and add a package". Not "evaluate everything".
2. **Success, defined before you start.** One observable result: an exact output, an HTTP 200, a trace visible in a dashboard. Write it down. Do not change it halfway to make the run look better.
3. **The entry point.** Where a newcomer lands: usually the docs home or the "Quickstart" link on the homepage.

## 2. A clean environment

- A fresh empty temp folder, never inside a real project.
- Hide what this machine already has. The cheapest way: run every command with an empty home and a bare PATH, e.g. `env -i HOME=$SB/home PATH=/usr/bin:/bin TERM=dumb /bin/zsh -c '...'`. Use Docker (`docker run --rm -it python:3.12-slim`) or a new venv when the tool needs it. Never let an installer touch the user's real home folder or shell config.
- Write the environment down (OS, shell, runtime versions) with `--env` at init.
- Use only what the docs tell you. If you know a shortcut from training, don't use it; if the docs miss a step, that is a finding.

```
friction.py init <audit_dir> --tool "<name>" --goal "<goal>" --success "<exact result>" --docs <entry url> --env "<os, shell, versions, sandbox>" --redact "<sandbox path>=~"
```
`--redact` scrubs your sandbox path from everything saved. The home folder and login name are always scrubbed.

## 3. Follow the docs literally

For every page you open:
```
snapshot.mjs <url> <audit_dir> --links --copy --name 02-quickstart
```
It saves a screenshot, the page text (`snapshots/<name>.md`, read this instead of guessing), every code block, every link with dead ones re-checked in a real browser, and what each copy button really puts on the clipboard. Name snapshots in order (`01-`, `02-`) so the screenshots tell the story.

For every action, log it as you go, not afterwards:
```
friction.py step <dir> --url <page> --action "Open the quickstart from the home page" --shot screenshots/02-quickstart.png
friction.py run  <dir> --url <page> --action "Install the SDK" --cwd <work> --show "pip install foo" -- "<real wrapped command>"
friction.py step <dir> --url <page> --action "Write app.py from the docs snippet" --loc 6
friction.py run  <dir> --url <page> --action "Run the example" --cwd <work> --show "python app.py" --success-if-ok -- "<command>"
```
`run` executes the command, saves the output to `outputs/`, times it, and marks a non-zero exit as an error. `--show` is what the developer typed when your real command is wrapped in a sandbox.

When something goes wrong or feels wrong, tag it right away with a fix:
```
friction.py amend <dir> 4 --tag missing-step --sev 2 --note "what happened, quoting the output" --fix "the exact text or change that would have prevented it"
```
Tags: `missing-step`, `wrong-snippet`, `unclear-error`, `version-mismatch`, `auth-wall`, `naming-confusion`, `slow-feedback`, `dead-link`, `copy-paste-hazard`, `other`. Severity: 1 annoying, 2 costs real time, 3 likely to make people quit.

Rules while following:
- Do exactly what the page says, in order. When the docs are wrong, first log what happens when you follow them, then recover the way a newcomer would (reread the output, search the same docs) and log each recovery step. Leaving the docs for GitHub issues or a search engine is a context switch: log it with its URL.
- Copy code with what the copy button gives (the `--copy` result), not a cleaned-up version.
- Count lines of code you write or edit with `--loc`.

## 4. Walls: stop and ask

Never type real credentials, card details, or a phone number, and never create an account on the user's behalf. When the path needs a signup, an API key, a card, or an approval:
1. Log it: `friction.py step <dir> --url <page> --action "Needs an API key" --outcome blocked --tag auth-wall --sev <n> --note "..."` with a screenshot. Note what the wall asks for, whether there is a free tier or test mode, and how many steps it adds.
2. Ask the user whether they want to get a key themselves and put it in an env var for you, or whether the audit ends at the wall. A wall with no sandbox key or test mode is itself a top finding.

## 5. Break it on purpose: three error checks

After success (or at the wall), make three common mistakes and grade what the tool says. Pick the three most likely for this tool, usually: a wrong or expired key, a missing env var or config, and a wrong version (old runtime, incompatible package). For a tool without keys, use a typo in a name and a wrong file or path instead.
```
friction.py errcheck <dir> --mistake "Wrong API key" --cwd <work> --show "FOO_KEY=bad python app.py" -- "<command>"
friction.py grade <dir> 1 --what 2 --why 1 --fix 0 --note "what a newcomer would think" --better "a rewritten message that would score 6/6"
```
Each of what happened, why, and how to fix is scored 0 (missing or wrong), 1 (partly, or buried), 2 (clear and early). Test the fix the message suggests before you score it.

## 6. Write the teardown

```
friction.py metrics <dir>     # check the numbers
friction.py render <dir>      # audit.md skeleton, timeline.svg and timeline.png
friction.py reel <dir>        # optional: journey.mp4 from the step screenshots (ffmpeg, or $FFMPEG)
```
Look at `timeline.png` before using it. Then fill every TODO in `audit.md`:
- **Summary:** did a newcomer reach the goal, how long it took, where it hurt most, the one change that helps most.
- **The journey:** a few short paragraphs under the table, quoting exact output and linking screenshots.
- **Top 5 fixes:** ranked by impact over effort. Each has the current text, the problem in one sentence, and a rewritten doc snippet or error message ready to paste.
- **What they do well:** specific, with step numbers. Name what to keep so the fixes don't break it.

Deliverables in `<audit_dir>`: `audit.md`, `friction.json`, `timeline.png`, `screenshots/`, `snapshots/`, `outputs/`, and optionally `journey.mp4`. Do not publish `.redact.json`; it holds the private paths.

## Tone

Write for the company's DevRel team, so it can be published or sent as is. Be fair and specific. Credit what is good, and say it first if it is the bigger story. Every complaint comes with a fix. Quote output instead of describing it. No sarcasm, no "obviously", no guessing at internal reasons. Plain words, complete sentences. If the tool did well, say so plainly: a short teardown of a good tool is a good result.

## Before you hand it over

- Every number in the summary comes from `metrics`, and the time model is stated (render adds it).
- Every friction point has a URL, quoted output and a fix. Every error grade had its fix tested.
- No real keys, personal paths, or user names anywhere (`grep -r "$HOME" <dir>` finds nothing).
- Show the user `audit.md` and the timeline. Sending it to the company is the user's call.
