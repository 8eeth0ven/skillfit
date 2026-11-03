---
name: post-launch
description: The moment DNS moves and for the thirty days after — verifies the cutover (DNS propagation, certificate, http and www redirects, the noindex, robots and sitemap on the live host, every redirect the audit mapped, forms, analytics, the staging copy, the old host, security headers), diffs production against the pre-launch baseline, and schedules the watch. Use when asked did the launch work, is the site live, what should I check after launch, the domain just switched, or when a site went live in the last month and something looks wrong. It is read-only and exits 0 whatever it finds.
---

# post-launch

The watch. It runs the moment DNS has moved, and then once a day for thirty days. It reports; it
never gates, never fixes, and never announces anything.

## The one rule

**Blockers are read first and announced last.** Nothing about a launch is announced — no email, no
post, no client call — until this report comes back clean. An announcement is the only step of a
launch that cannot be taken back, and the two blockers here are exactly the two states where the
launch has not really happened: a certificate nobody can get past, and a noindex telling search
engines to forget the site. Both look fine in a browser you are already logged into.

If somebody asks you to announce while a blocker stands, say plainly what the blocker is and what
it costs, and do not soften it.

## Read-only

The skill is read-only. It fetches the live site, the staging host, the old host and the urls in
the redirect map, and it asks four public DNS resolvers where the domain points. It writes exactly
two things, both the operator's own record: the report bundle, and `watch.json` inside it. It never
edits a site, submits a form, flips a setting, calls a provider API or touches DNS.

Three rules follow, and you restate them when you report:

1. **Evidence for every finding.** A url, a status, a header, a DNS answer, a csv line.
2. **A skip is not a pass.** Every input you did not supply becomes a named line in **Not covered**.
3. **`Not covered` is never a pass.** You repeat that section to the human verbatim.

## The two modes

| Mode | When | What it answers |
|---|---|---|
| `--mode cutover` | the moment DNS has moved, and after any fix | did the launch actually happen |
| `--mode watch` | once a day, days 1–30 | what is due today, and has anything drifted |

Run `cutover` first, fix what it finds, run it again until it is clean, **then** announce. Start the
watch the same day.

## 1. Gather the inputs

Every input you leave out becomes a check that cannot run. Ask for each one; do not guess.

- **The production url.** Required.
- **`baseline.json`** — from the `pre-launch` bundle, or from a `launch-audit` run against staging
  before the cutover. This is what "did anything change" is measured against. Without it, four
  checks have nothing to compare and a fifth falls back to `--expect-analytics`. All of them say so.
- **`redirects.csv`** — from the `launch-audit` bundle built with `--old-url`. Every row is
  re-requested at the url it was written with.
- **The old site's url**, if one is being replaced.
- **The staging url**, so the run can confirm the staging copy is now sealed.
- **The analytics measurement id**, for when there is no baseline.
- **The DNS records that were supposed to be in place**, as `apex=` and `www=` values.

If you do not have the baseline or the redirect map, say so before you run rather than after: they
come from the two earlier phases, and after the cutover neither can be recreated.

## 2. Run the cutover check

Run the script; never read its source, and never reimplement what it does.

    node scripts/post-launch.mjs --mode cutover --url <production url> \
      --baseline <path to baseline.json> --redirects <path to redirects.csv> \
      --old-url <old site url> --staging-url <staging url> \
      --expect-analytics <measurement id> --expect-dns apex=<ip>,www=<host> --out <dir>

The path is relative to this skill's own directory — run the command from there. The bundle is
written under the **current working directory**: without `--out` it lands in
`./website-launch/<host>-post-launch-<date>/`, which with the command above means inside this
skill's own directory. Write the bundle wherever the work lives with `--out`.

Other flags: `--dev-host <host>` (repeatable), `--browser auto|on|off`, `--out <dir>`,
`--config <path>`, `--json`, `--help`.

**Exit codes:** `0` always, however bad the cutover is. `2` for a usage error or an IO failure.
Exit 0 never means "the launch is fine" — this reports, it does not gate. Read the report.

## 3. Read the report in this order

`references/reading-the-report.md` has the bundle layout. `references/cutover-day.md` explains why
the day runs in the order it does — read it before you start fixing things out of order.

1. **The blockers.** Printed bolded, first, whatever step of the day they came from. Fix these
   before anything else and before anybody is told the site is live.
2. **The high findings.** Redirect drift, a missing page, a dead form endpoint, a live staging
   copy, the old host still serving — each of these is a thing losing traffic or enquiries right
   now. They are today's work, not this week's.
3. **The baseline diff.** `references/baseline-diff.md` says which fields are expected to move at
   a launch and which never are. Do not report the whole diff as damage; report the parts nobody
   asked for.
4. **Medium and info.** Read them. Say what they are. Do not fix them today.
5. **Not covered, verbatim.** Every line, unedited, including the two things no crawl can see.

Then re-run, and keep re-running until the blockers are gone.

## 4. Work the six human items

They print at the end of every run and they are not optional:

    submit the sitemap (Search Console and Bing)   ·   request indexing for the top pages
    confirm the new Search Console property        ·   verify analytics in real time
    keep the old host up and redirecting           ·   announce only after this is clean

Never tick one off on somebody's behalf. "The endpoint returned 200" is not "a person received the
test submission", and "the tag is in the HTML" is not "a hit appeared in real time".

## 5. Run the watch, daily

    node scripts/post-launch.mjs --mode watch --url <production url> --day <n>

It prints what is overdue, what is due today and what is coming in the next seven days, then
re-runs the automated part and records the run. `references/thirty-day-watch.md` has the whole
schedule, what to look at in Search Console and analytics on each day, and what "healthy" looks
like so a normal post-launch dip is not reported as a disaster.

Leave `--day` off and it counts from the first run. A day the watch never ran stays overdue for the
automated tasks until a run covers it; a human task stays overdue until a human clears it, because
nothing a script does is evidence that somebody opened Search Console.

## 6. Day 30

Two things, and neither is automated:

- **The retrospective.** What regressed, what the redirect map missed, and what to add to the
  `pre-launch` gate so the next launch does not repeat it. Write it down.
- **The old-host decision.** The old host may be decommissioned only once Search Console shows no
  crawl of old urls **and** the redirects have been in place for at least thirty days. Until both
  are true, keep paying for it. Turning it off early throws away every link the old site earned.

## 7. Present the result

Lead with the decision, not a count.

1. **The verdict.** "The cutover has one blocker" or "The cutover is clean." One sentence.
2. **What blocks it**, with the fix named.
3. **What is bleeding**, grouped by cause: the high findings, in plain language.
4. **What changed against the baseline** that nobody asked for.
5. **Not covered, verbatim.**
6. **The human items**, with what is done and what is not.
7. **Whether the launch may be announced.** Say it explicitly, either way.

## The two checks that never run

- **Copy vs. source documents.** Nothing compares the words on the live pages against the signed-off
  copy. A person has to read both.
- **Pages vs. agreed scope.** Nothing knows which pages were supposed to exist. A page that was
  never built is invisible here.

## References

| File | Covers |
|---|---|
| `references/cutover-day.md` | The ordered day script, and why each step sits where it does |
| `references/thirty-day-watch.md` | The schedule, what to read in Search Console and analytics, what healthy looks like, the old-host rule |
| `references/baseline-diff.md` | Every diff field, which changes are expected at a launch and which are not |
| `references/reading-the-report.md` | The bundle, the severities, the ids, how to triage |

## Where this sits

`pre-launch` gates the repository before deploy and blocks. `launch-audit` crawls a staging or live
url and reports. `post-launch` is this one: the cutover and the thirty days after it. Run them in
that order — the baseline and the redirect map this skill needs can only be made by the first two,
and only while the old site is still up.
