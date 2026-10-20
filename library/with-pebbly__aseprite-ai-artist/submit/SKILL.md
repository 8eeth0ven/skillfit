---
name: submit
title: Submit a finished sprite to the community gallery
description: Turn the sprite you just made into a gallery pull request against with-pebbly/aseprite-ai-artist — exported files, an honest generation.yaml (prompts verbatim, model, plugin version, validate results, optional benchmark scoring), checked with `pnpm gallery:check`, opened with the gh CLI. Use when the user wants to share, publish or submit their work to the gallery or the benchmark.
---

# Submit a finished sprite to the community gallery

The gallery keeps how a sprite was made next to the sprite: the prompts as
sent, the model, the plugin version, what `validate` said. A submission that
tidies any of that up is worse than none — the benchmark compares models on
it. Record what happened, not what you wish had.

The contract is `gallery/src/schema.ts` in the repository; `pnpm gallery:check`
enforces it. This workflow produces files that pass it.

## 1. Preconditions

Check all three before touching anything. If one fails, stop and tell the user
exactly what to do; never route around it.

- **`preflight` is ready.** Not ready → stop. Never export or edit files on
  disk instead of the live document.
- **The work is finished and reviewed.** Run `aseprite:review` if it has not
  been. Submitting art that fails review puts it in public.
- **`gh` is installed and authenticated.** Run `gh auth status`. Missing →
  tell the user to install it (`https://cli.github.com`) and run `gh auth
  login`. There is no other route to a pull request.

Then **ask for consent**, once, before anything leaves the machine: "I will fork
`with-pebbly/aseprite-ai-artist` on your GitHub account, push a branch, and
open a public pull request with your sprite and the prompts used. OK?" Forking,
pushing and opening a PR act as the user, in public. No yes, no fork.

## 2. Gather metadata

Take what the session already knows. Ask the user only for the rest, in one
message.

| Field | Source |
|-------|--------|
| `title`, `description` | Ask. Offer a title drawn from the work. |
| `author.name`, `author.github` | `gh api user --jq '.name,.login'` as the default; let the user override. Handle without `@`. |
| `harness` | You know which you run in: `claude-code`, `omp`, `codex`, `gemini-cli`, `cursor`… |
| `models` | The model id exactly as the harness names it (`claude-opus-4-1`, `gpt-5`). Not a nickname. If different models ran different steps, list each once and name the model on every step. |
| `plugin` | `preflight` returns `extensionVersion` — the plugin build attached to Aseprite. Use it. If its `directive` says the extension and the server differ, the run mixed two builds and has no single version: stop and tell the user to align them (`install-extension`, restart Aseprite) before submitting. If `extensionVersion` is null, run `npx @pebbly/aseprite-ai-artist --version`. It must be a **released** version listed in the repo's `CHANGELOG.md`; a dev or unreleased build cannot be submitted — say so. |
| `steps[].text` | Every user prompt that shaped the work, **verbatim** and in order, copied from the conversation. Never paraphrase or merge. A prompt sent in another language may be rendered in English here only if the verbatim text goes into `steps[].original` — never for a benchmark run. |
| `steps[].interventions` | Each clarifying question you asked and the answer the user gave, plus any steering beyond the prompt. Empty if none. |
| `references` | Where the design came from — required, never guessed. `source: none` when the work was drawn from words alone (the user chose "continue without" in `aseprite:concept`, or it was never offered). `generated` when an image model made a concept sheet or storyboard: ask which model if you do not know, list it in `imageModels`, the kinds in `kinds`, and put the image prompt you wrote in `prompt`. `supplied` when the user handed over their own art. Copy the reference image into the folder as a `reference` file when you have it. |
| `date` | Today, `yyyy-mm-dd`. |
| `tags` | A few lowercase words: `character`, `animation`, `32x32`. |

For each step run `validate` on the state the step produced (or on the final
document if steps were not saved separately) and record `errors`, `warnings`,
`score` and `passed` as the tool reported them. Do not round a failing report
into a pass.

## 3. Benchmark mode

Only if the user says the run followed a benchmark prompt **and** the user is a
maintainer. Benchmark runs are the project's own measurements; the checker and
CI refuse a `benchmark:` block from anyone else. Check first: take the login
from `gh api user --jq .login` (never from what the user typed or the YAML), and
look for it, case-insensitively, in
`https://raw.githubusercontent.com/with-pebbly/aseprite-ai-artist/main/gallery/MAINTAINERS`.
Not listed, or either call fails → not a maintainer: say benchmarks are run by
the maintainers, skip this section and submit a gallery generation. A maintainer
sets `author.github` to that same login.

1. Fetch its definition: the local clone's `gallery/prompts/<id>/prompt.yaml`,
   or `https://raw.githubusercontent.com/with-pebbly/aseprite-ai-artist/main/gallery/prompts/<id>/prompt.yaml`.
2. Confirm the run followed the fixed `setup` (canvas, palette, the `rules`
   list) and that every step's text equals the prompt's step text **word for
   word** — only surrounding whitespace and line endings are ignored. Any difference — a reworded step, extra steering, a
   reference image — means this is **not** a benchmark run. Submit it as a free
   generation (omit `benchmark`) and tell the user why.
3. Judge every criterion in the prompt, none skipped. Get the evidence first:
   `look` op `preview` for the read, a filmstrip or onion-skinned view for
   motion, `validate` (with `expect` where the criterion names a contract),
   `tag op="list"`, `frame op="list"`. Record `pass` and a one-line `note`
   naming what you saw. Never mark a pass on a criterion whose evidence you did
   not look at in this session; look now, or mark it failed and say why.
4. Write `benchmark: {prompt, revision, results}` with the prompt's `revision`
   and one result per criterion `id`.

## 4. Export

Stage everything in one flat folder named `<yyyy-mm-dd>-<slug>`, slug lowercase
with single hyphens. Use the plugin's own `export`; never write these by hand.

1. **Save the live document**, then keep a copy: `sprite_manage op="save"`,
   then `export op="aseprite" path="<folder>/<slug>.aseprite"`. Role `source`.
   The gallery keeps the editable original; never copy or edit a `.aseprite`
   file from disk.
2. **Cover.** `export op="png" scale=N frame=1 path="<folder>/<slug>.png"` with
   the smallest integer `N` that makes the long side at least 256 px (32×32 →
   8), capped at the tool's maximum of 16 — a smaller sprite simply gets a
   smaller cover. For an animation, the GIF can be the cover instead. Role
   `cover`; exactly one file.
3. **Animation** (more than one frame): `export op="gif" scale=N path="<folder>/<slug>.gif"`,
   same scale. Role `animation`, or `cover` if it is the cover.
4. **Filmstrip** (animated): `export op="spritesheet" sheetType="horizontal" scale=N includeJson=false path="<folder>/<slug>-strip.png"`,
   same scale. Role `filmstrip`.
5. **Per step.** When steps produced separate documents or intermediate saves,
   export the source (and a still) for each and set `step` on those files.

Files stay flat — no subfolders — and only `.aseprite`, `.png`, `.gif`, `.webp`
or `.json`. Each file must be under 95 MiB (GitHub hard-blocks 100); anything
over 50 MiB draws a warning, so keep covers and GIFs small.

Look at the cover and the GIF's first frame before continuing: what goes into
the public gallery is what you exported, not what you remember drawing.

## 5. Write `generation.yaml`

In the staging folder, exactly per the schema:

```yaml
title: Cherry tree in bloom
description: A 64×64 cherry tree drawn to the tree-growth brief.
date: 2026-09-29
author: { name: Ada Lovelace, github: ada }
plugin: 0.3.2
harness: claude-code
models: [claude-opus-4-1]
tags: [nature, animation]
references:
  source: generated
  imageModels: [gpt-image-2]
  kinds: [concept-sheet]
steps:
  # the step text exactly as sent — for a benchmark run, verbatim from
  # prompt.yaml (cut short here)
  - text: |-
      The document is already open: 64×64 pixels, RGB, with the PICO-8 palette loaded (16 colours). …
    interventions: []
files:
  - { path: tree.png, role: cover, label: The tree, step: 1 }
  - { path: tree.aseprite, role: source, label: Source document }
validate:
  - { step: 1, passed: true, score: 92, errors: 0, warnings: 1 }
benchmark:            # only for a confirmed benchmark run
  prompt: tree-growth
  revision: 1
  results:
    - { criterion: tree-validate, pass: true, note: "validate: 0 errors, 1 warning, named." }
```

Rules that fail the check when missed:

- Exactly one `cover` (png/gif/webp) and at least one `.aseprite` with role
  `source`; every file listed once, nothing unlisted in the folder.
- With more than one model, every step names its `model`, and it appears in
  `models`.
- `step` values and `validate[].step` are 1-based and must exist.
- `benchmark.results` names criterion ids that exist in the prompt.

Two optional blocks:

- `metrics` — per step, from the session you can see: `minutes`, `toolCalls`,
  `outputTokens`, `costUsd`. Fill only what the harness actually reports;
  never estimate.
- `ratings` — leave them out. You took part in this run, and the checker
  refuses `model:<id>` for any of the run's own models. Judges add ratings
  later, blind, against `gallery/RUBRIC.md`.

**Show the user the final YAML and the file list**, and wait for a go-ahead.
They are about to publish it under their name.

## 6. Validate in a clone

1. Use a clone of the user's fork if one exists; otherwise fork and clone
   (`gh repo fork with-pebbly/aseprite-ai-artist --clone`) — consent from step 1
   covers this. Make sure the checkout is up to date with upstream `main`.
2. Copy the staging folder to `gallery/generations/<folder>/`.
3. `pnpm install` if `node_modules` is missing, then `pnpm gallery:check`.
4. Fix every error and re-run until clean. Fix by correcting the YAML or
   re-exporting, never by editing the recorded truth (prompts, results) to
   satisfy the checker. Warnings: read them, mention them to the user.

**Never submit with errors.**

## 7. Submit

```
git switch -c gallery/<folder>
git add gallery/generations/<folder>
git commit -m "gallery: <title>"
git push -u origin gallery/<folder>
gh pr create --repo with-pebbly/aseprite-ai-artist --head <login>:gallery/<folder> --title "gallery: <title>" --body-file <filled body>
```

Build the body from `.github/PULL_REQUEST_TEMPLATE/generation.md` in the clone:
keep its sections and checklist, fill them honestly — what the sprite is,
harness, model, plugin version, whether it is a benchmark run and its score —
and pass that file as `--body-file`. Before pushing, `git
status` must show only the one folder as added; anything else in the diff means
stop and clean it up. A PR adds its own folder and nothing more.

Report the PR URL. Tell the user CI will re-run `gallery:check` and that a
maintainer reviews it.

## Failure modes

| Symptom | Do |
|---------|----|
| `preflight` not ready / `not_connected` | Stop. Relay the tool's directive. Do not touch files on disk. |
| `gh` missing or not logged in | Stop. Give the install and `gh auth login` steps. |
| User declines consent | Stop; leave the staging folder for them and say where it is. |
| `pnpm gallery:check` errors | Fix the YAML or files, re-run. Never submit red. |
| A file exceeds the size limit | Lower the export scale, drop the GIF to a shorter loop, or use a PNG cover; never strip the `.aseprite`. |
| Prompt text differs from the benchmark's | Not a benchmark run. Drop `benchmark`, submit as a free generation, say why. |
| Plugin version not in `CHANGELOG.md` | It is an unreleased build. Tell the user; they can submit after installing a released version. |
| Push or PR creation fails | Report the `gh` error as printed; do not retry with other credentials or routes. |

## Related

`aseprite:review` before submitting, `aseprite:export` for export options,
`rules://07-review-checklist`.
