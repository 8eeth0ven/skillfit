---
name: codebase-map
description: Understand an unfamiliar codebase fast, the way senior engineers do. Reads the orientation signals (README, manifests, CI, Dockerfiles, routes, migrations), mines git history for hotspots, hidden coupling and ownership, builds the import graph to find layers, cycles, load-bearing and dead code, then traces one real request or command end to end by actually running it. Writes MAP.md with a one-paragraph purpose, a Mermaid architecture diagram, the traced path as file:line hops, hotspot and coupling tables, a glossary, gotchas and first tasks, plus an optional SVG. Use when the user says "explain this codebase", "I'm new to this repo", "map the architecture", "onboard me", "where does X happen", "how is this project structured", or joins a new team or project.
---

# Codebase map

Reading files top to bottom is the slow way in. Senior engineers ask four questions instead, in this order: **what does it do, how is it run, where does the important work happen, and what path does one real request take.** The first three come from cheap signals (manifests, CI, git history, imports). The fourth only comes from running the code. Everything ends up in one file, `MAP.md`, that a new person can read in ten minutes.

Work **read-only** on the repo. Put every output in a temp folder (`out=$(mktemp -d)`) unless the user asks for `MAP.md` in the repo. Never run migrations, deploys or anything that touches a shared database or real credentials.

Scripts are in `scripts/`, Python 3.9+ standard library and git only. `S=~/simcraft/skills/coding/codebase-map/scripts`.

## 0. Ask one thing

"Is there a specific thing you need to do here (fix a bug, own an area, review a change), or a general map?" A goal decides which path to trace. If there is no answer, map the whole repo and trace its most important user action.

## 1. Orient (15 minutes)

```
python3 $S/entrypoints.py <repo> > $out/entry.md
```
It lists docs to read first, build and run commands (package.json scripts, console scripts, Makefile, Procfile, Dockerfile CMD, compose services), CI pipelines and the commands they run, mains, servers, CLI commands, HTTP routes, background jobs, the data model, environment variables (with a flag when the `.env` template is missing one), and tests. Every hit is `file:line`.

Then read, in this order: README and contributor docs, **the CI file** (it is the only build recipe that is known to work), the main manifest, the entrypoint files. Write the **one-paragraph purpose** now, before reading more code: who uses it, what goes in, what comes out, what it talks to.

## 2. The data model is the backbone

Read the schema before the logic. Migrations (oldest shows the original core, newest shows where the product is going), ORM models, Prisma or SQL files, or, if there is no database, the main data shapes (pydantic models, TS types, JSON files on disk). Write down the 3 to 7 core entities and how they relate. Most business logic is "load these, change them, save them", so knowing the nouns makes the code readable.

## 3. Structure from imports

```
python3 $S/deps.py <repo> --json $out/deps.json --mermaid $out/deps.mmd --svg $out/deps.svg > $out/deps.md
```
Read: the **layers** (level 0 is the foundation, top is entry code), **folder cycles** (tangled modules, with the cheapest edge to cut), **load-bearing files** (most importers: change carefully), **possibly dead files** (no importers), and the main external packages. If one folder holds most of the code, run again with `--under <that folder>` to see inside it.

## 4. History: where the work and the risk are

```
python3 $S/hotspots.py <repo> --deps $out/deps.json > $out/hot.md
```
- **Hotspots** (changes x complexity): the few files where most bugs and most of your future work will be.
- **Change coupling**: files that change in the same commits. A pair with `import link = NO` is a hidden dependency, for example two copies of the same logic, or a client and server that share a format. These are the best gotchas.
- **Ownership** and **knowledge at risk**: who to ask about each area, and complex files whose main author has gone quiet.
- **Bug magnets**, **frozen code** and **new code**.

Add `--anonymize` if the map will be shared outside the team. Under about 30 commits, git signals are weak: say so and lean on steps 3 and 5.

## 5. Trace one real path by running it

This is the step that turns guesses into knowledge. Pick one real user action (the one the top hotspots serve, or the user's goal). Get it running using the CI steps. Then either:
- find the **sink** (the DB write, the HTTP response, the output file), put a stack dump or breakpoint there (`breakpoint()`, `traceback.print_stack()`, `console.trace()`, `debug.PrintStack()`), trigger the action once, and read the stack bottom-up; or
- for Python, run it under the tracer: `python3 $S/trace_py.py --repo <repo> --out $out/trace.txt -- <script or -m module> <args>`. It prints every repo function the run touched, by depth, as `file:line`.

If the path calls paid or external services, stub them at the edge (patch the HTTP call to return a canned response) instead of using real keys. Record each hop as `file:line  what happens here`, and mark anything surprising.

## 6. Load-bearing vs dead

Load-bearing = many importers, on the traced path, or a hotspot. Dead candidates = no importers and frozen for a year. Before calling anything dead, grep for its name as a string (plugin registries, `getattr`, dynamic imports, config files, framework conventions). Say "probably dead, because..." rather than "dead".

## 7. Write MAP.md

Use the template in [reference.md](reference.md#mapmd-template): purpose, how to run it, architecture diagram (Mermaid, drawn from what you learned, not just the raw import graph), the traced path, data model, hotspots, coupling pairs, who knows what, glossary, gotchas, first tasks. Mark each claim **ran** (you saw it happen) or **read** (from the code). Then check every reference:
```
python3 $S/check_map.py $out/MAP.md <repo>
```
Fix every broken one. Finish with a five-line summary in chat and the path to `MAP.md` (and the SVG if made).

## Rules

- Never claim a hop you did not see in code or in a run. A wrong map is worse than none.
- Explain jargon the first time it appears, and put every project-specific term in the glossary.
- First tasks must be small, real and safe: a test to add for a hotspot, a log line on the traced path, a dead file to confirm.
- Depth, per-language tracing recipes, heuristics and their limits: [reference.md](reference.md). A real example: [examples/MAP.md](examples/MAP.md).
