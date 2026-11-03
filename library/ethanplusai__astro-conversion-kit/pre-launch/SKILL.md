---
name: pre-launch
description: Gate a website launch from its repository — repo hygiene, placeholders and leaked dev hosts, the production build, the build output (404 page, internal references, icons, social cards, robots, sitemap, canonicals, titles, headings), framework configuration, and redirect coverage for the site being replaced — then walk the human checklist no script can verify. Use before any site launch, before a DNS cutover, when a site is replacing an existing one, or when somebody asks whether a site is ready to launch. Read-only apart from its own report and a progress file; it exits 1 if anything fails.
---

# pre-launch

The gate. It inspects the repository and the build, and it blocks the launch if anything
mechanical is wrong. Then it hands you up to nine things no script can check.

## The two rules

**Never declare the site ready while any check fails.** There is no flag that turns a failure into
a warning, and adding one would be the wrong fix. Exit 1 means not ready. If you believe a check is
wrong about this site, say so plainly to the human and fix the check — do not route around it.

**Never reorder the human list.** Its order is a dependency order with two one-way doors in it:
the Search Console baseline must be exported **before DNS moves**, and the forms must reach a real
person **before the deploy** that makes them public. Both are unrecoverable if taken late.

## Read-only

The gate is read-only with respect to the site. It reads the repository, runs the project's own
build command, and fetches the predecessor site's sitemap when you give it one. It writes exactly
two things of its own, both the operator's record: the report bundle, and `.launch-progress.json`
in the repository being gated (only when you pass `--confirm` or `--reset-progress`). It never
edits the site, submits a form, flips a setting, calls a provider API, or touches DNS.

The one exception is deliberate: unless you pass `--skip-build`, the gate runs the project's own
build script, so whatever that build writes — `dist/`, a cache, packages it installs — is written,
because it is the project's build. Say so if somebody asks whether the gate is safe to run.

Three rules follow from that, and you restate them when you report:

1. **Evidence for every finding.** A file path, a line, a url, an exit code.
2. **A skip is not a pass.** Every skipped check carries a reason and appears in **Not covered**.
3. **`Not covered` is never a pass.** You repeat that section to the human verbatim.

## 1. Gather the inputs

Ask for anything you do not already know. Do not guess any of these.

- **The production url.** Required. Every host comparison in the gate is against it. A gate run
  against the wrong host reports confidently and means nothing.
- **Is this replacing an existing site?** If yes, get the old site's url. The gate fetches its live
  sitemap, and that can only happen **while the old site is still reachable** — usually before DNS
  moves. After the cutover this check can never be run.
- **Environment variables the production build needs.** Names only, never values.
- **Any internal or preview hostnames** that might have leaked into the build.
- **Where the build output goes**, if it is not `dist`, `out`, `build`, `_site` or `public`.

A repository may already answer these in a `.launch.json` — see `references/config.md`. If one
exists, read it and confirm it is current rather than re-asking.

## 2. Run the gate

Run the script; never read its source, and never reimplement what it does.

    node scripts/pre-launch.mjs --dir <repo> --production-url <url> --out <dir>

The path is relative to this skill's own directory — run the command from there, and point
`--dir` at the repository being launched. The bundle is written under the **current working
directory**, not under `--dir` and not next to the skill: without `--out` it lands in
`./website-launch/<host>-pre-launch-<date>/`, which with the command above means inside this
skill's own directory. Write the bundle wherever the work lives with `--out`.

Other flags: `--predecessor-url <url>`, `--build-dir <dir>`, `--required-env <NAME>` (repeatable),
`--dev-host <host>` (repeatable), `--ignore-dir <dir>` (repeatable), `--strict`, `--skip-build`,
`--out <dir>`, `--config <path>`, `--json`, `--help`.

`--ignore-dir` is for a folder committed alongside the site that is not the site, such as the raw
HTML captured from the old site during a conversion (`--ignore-dir capture`). The path is relative
to `--dir`. The repository scans (nested git, committed secrets, placeholder source) skip it;
`hygiene.env-tracked` still catches a tracked `.env` inside it, and **Not covered** says
`ignored by request: <dirs>` (a folder that does not exist is marked `(not present)`). The build
folder is what deploys, so an `--ignore-dir` that is, holds or sits inside it is refused with exit
2, and every build-output check reads it in full. It is never a way to quiet a finding about the
site itself: see "Never suppress" below.

It runs the project's build first, so the output it inspects is never stale. Use `--skip-build`
only when you have just built and nothing has changed since.

**Exit codes:** `0` passed, `1` at least one check failed, `2` a usage or IO error.

## 3. Triage — every failure blocks

Read `report.md` in the bundle it names. `references/reading-the-gate.md` has the status table and
the bundle layout. Then, in this order:

1. **Read every failing check before fixing anything.** Thirty failures from one template is one
   fix, and you cannot see that one at a time.
2. **Fix causes first.** If `build.succeeds` failed, every `output.*` result is meaningless — they
   read whatever was on disk from last time. Fix the build, rerun, read again.
3. **Fix what you can, in the repository.** Placeholder ids and copy, missing environment
   variables, a wrong site url in the generator config, a missing redirect entry, an og:image at
   the wrong size, a missing canonical — these are yours to fix. Do them.
4. **Never suppress.** Do not add a flag, do not edit a check to pass, do not exclude a file from a
   scan to quiet it. If a check is genuinely wrong, correct the check in the source and tell the
   human you did.
5. **Rerun until the gate passes.** A partial pass is not a pass.

An **advisory** result does not block. Report it, do not fix it silently, and do not describe it as
a failure. A **skip** is not a pass either — read its reason and decide whether the thing it could
not check still needs a human.

## 4. Walk the human checklist, one item at a time

Only after the gate passes. The full text for each item — why it matters, how to verify it, and
what "done" looks like — is in `references/human-checklist.md`. Read the item before you ask.

Work **one at a time**. Ask, wait for an actual answer from the person who owns the thing, and only
then record it:

    node scripts/pre-launch.mjs --dir <repo> --confirm <id>

    node scripts/pre-launch.mjs --dir <repo> --progress

`--progress` prints the list with ✓ and ☐, so a session that ends halfway resumes where it stopped.
`--reset-progress` clears it. Pass `--predecessor-url` (or `--config`) to these commands too — the
list is conditional, and without it `gsc-baseline` is not offered and "every item is confirmed"
would be premature.

Never confirm an item on somebody's behalf. Never confirm one because it is probably fine. "The
endpoint returns 200" is not a confirmed `forms` item; a named human saying "yes, I received it in
the inbox I read" is.

The ids, in their fixed order:

    forms  analytics  hosting  payments  legal  gsc-baseline  dns  signoff  rollback

`payments` appears only when the repository uses a payment SDK. `gsc-baseline` appears only when
you gave a predecessor url.

## 5. If a site is being replaced

Read `references/predecessor-redirects.md` before you touch the redirect map. The method in one
line: the old sitemap is the source of truth, keep the same path wherever you can, one explicit
301 per url that moved, no wildcards over content, no chains, take the Search Console export
before DNS moves, keep the old host up through propagation, and do not delete the old sitemap.

The single most common mistake is a wildcard that looks like coverage: `/legacy/*` to the homepage
answers forty old articles with one page, returns 200 for all of them, and loses every ranking.
The gate fails it and quotes the rule.

## 6. Present the result

Lead with the decision, not a count.

1. **The verdict.** "The gate fails: six checks" or "The gate passes." One sentence.
2. **What blocks it**, grouped by cause rather than by check, with the fix named. "Every page is
   missing a canonical — it is one layout, so it is one fix."
3. **Advisories**, marked clearly as not blocking.
4. **Not covered, verbatim.** Every line, unedited. Never summarise it, never call it minor, never
   leave it out because the list is long.
5. **The human checklist**, with what is confirmed and what is next.

## The two checks that never run

Every report ends with these, and they are there because they are the two failures that hurt most
and that no checker can reach:

- **Copy vs. source documents.** Nothing here compares the words on the pages against the
  signed-off copy. Somebody has to sit with both and read.
- **Pages vs. agreed scope.** Nothing here knows which pages were supposed to exist. A page that
  was never built is invisible to a checker.

Say both out loud. A repository can pass every check in this skill and still be missing half of
what was agreed.

## References

| File | Covers |
|---|---|
| `references/reading-the-gate.md` | The four statuses, the six groups, the bundle, how to triage |
| `references/human-checklist.md` | Each item: why it matters, how to verify it, what done looks like |
| `references/predecessor-redirects.md` | The migration method: sitemaps, same-path, wildcards, chains, the baseline |
| `references/framework-hints.md` | What the detector reads per stack, the redirect formats, how to fix each hint |
| `references/config.md` | The `.launch.json` schema, with an example and what not to put in it |

## Where this sits

`pre-launch` is this one: it runs against the repository before deploy and it blocks.
`launch-audit` crawls a staging or live url and reports without blocking. `post-launch` runs the
moment DNS moves and diffs production against the baseline. Run them in that order.
