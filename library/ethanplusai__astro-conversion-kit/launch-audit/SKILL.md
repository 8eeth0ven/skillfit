---
name: launch-audit
description: Audit a live or staging website and report what would go wrong at launch — crawl and inventory, indexability, redirects for a domain cutover, links, images, forms, accessibility, performance, analytics, content sanity, and full-page screenshots for a visual pass. Use before or right after a site launch, when asked to QA, audit, or review a website, when a site is moving to a new domain, or when somebody asks whether a site is ready to go live. Read-only: it never submits a form, clicks a control, or edits anything.
---

# launch-audit

Crawl a staging or live site, gather evidence, and hand a person a report they can act on.

## The golden rule

**Read-only, report-only.** Nothing in this skill edits a site, submits a form, flips a setting,
writes to a provider API, or clicks a destructive control. Every finding is a recommendation with
evidence for a human to act on.

Four more that follow from it, and that you restate when you present the report:

1. **No silent caps.** Every bound on coverage — max pages, depth, sampled pages, unverifiable
   externals — is reported by name in **Not covered**.
2. **Evidence for every finding.** A url, a status code, a header value, a screenshot path.
3. **`Not covered` is never a pass.** You repeat that section to the human verbatim.
4. **A skip is not a pass.** Every skipped check carries a reason.

## 1. Gather the inputs

Ask for what you do not already know. Do not guess any of these.

- **The url to audit.** Required.
- **Is it staging or live?** A staging target is expected to be noindexed; pass `--staging` so a
  site-wide noindex drops from blocker to informational. On a live target it is the blocker.
- **Is this replacing an existing site?** If yes, get the old site's url and pass `--old-url`.
  This must be done **while both sites are still reachable** — usually before DNS moves. It is the
  only moment a redirect map can be built automatically.
- **Any dev or staging hostnames that might have leaked** into the build. Pass each with
  `--dev-host`. A leaked hostname is a blocker and the audit can only search for the ones it knows.
- **Is Playwright installed?** If it is, the browser tier runs: screenshots, axe accessibility,
  Lighthouse, and whether analytics actually fires. If it is not, say so — roughly a third of the
  report does not happen, and the report says which third.

## 2. Run the script

Run it; never read its source, and never reimplement what it does. Everything it does is
read-only: it fetches pages, renders a sample of them, and writes a bundle to disk.

    node scripts/launch-audit.mjs --url <url> [--old-url <url>] [--dev-host <host>] [--staging] [--browser auto|on|off] [--out <dir>]

The path is relative to this skill's own directory — run the command from there, and write the
bundle wherever the work lives with `--out`.

Other flags: `--max-pages` (default 200), `--max-depth` (default 4), `--ignore-robots`,
`--baseline <path to an earlier baseline.json>`, `--json`, `--config <path>`, `--help`.

The browser tier defaults to `auto`: it runs if Playwright is present and is skipped with a reason
if it is not. Use `--browser on` to make its absence an error, `off` to skip it deliberately.

It exits 0 however many findings there are — this reports, it does not gate. Exit 2 means a usage
error. If it suggests installing Playwright, relay the suggestion; do not install anything without
being asked.

## 3. Read the bundle

The script prints the bundle path and writes:

    report.md        findings by dimension, then Ops & access readiness, then Not covered
    findings.json    the same findings, machine-readable
    crawl.json       every url reached, its status, depth and how it was found
    baseline.json    a snapshot for post-launch to diff against
    manifest.json    exactly which files this run wrote
    redirects.csv    one row per old url (only with --old-url)
    screenshots/     desktop, tablet and mobile per rendered page (browser tier only)
    lighthouse/      the scores and metrics Lighthouse measured, per page and form factor (browser tier only)

Read `report.md` first: blockers, then **Not covered**, then everything else. Knowing what was not
checked changes how you read a clean section. `references/reading-the-report.md` has the severity
table and how to work the bundle.

## 4. Do the three judgment passes yourself

The script gathers evidence for three reviews no checker can do. Do all three before you present
anything. Each one has a reference file; read it before the pass, not after.

**Screenshots** — per `references/reading-the-report.md`. Open the mobile and desktop shots of
each rendered page side by side and look for layout breakage, horizontal overflow, missing images,
clipped or truncated text, navigation that does not collapse at phone width, and placeholder
imagery that survived to launch. If no browser ran there are no screenshots, and this review did
not happen — say so rather than letting its absence read as a pass.

**Forms** — per `references/forms.md`. Classify every form in the inventory as first-party,
third-party or dead, using the evidence in the report. Then tell the human which forms need a test
submission and exactly what to confirm: the success message, the notification arriving in a
monitored **inbox** rather than a spam folder, and the record appearing wherever it is meant to.
You never submit a form yourself.

**Contact details** — per `references/content.md`. Collect every phone number, email address and
postal address the report found into one list, check the `tel:` links dial the numbers displayed
beside them, and ask the site's owner which are current. A second phone number left on one page
sends half the calls nowhere, and nothing can tell from outside which one is right.

## 5. Present the report

Structure your summary the way the report is structured, and lead with the decision rather than a
count. Forty low findings from one template is one fix; one blocker is a launch.

1. **What blocks the launch.** One plain sentence per blocker. If there are none, say so directly.
2. **Findings grouped by dimension, worst severity first within each.** Give the shape, not just
   the number: "fourteen pages are missing a description — it is one template, so it is one fix".
   Name the fix rather than the failure, and say what it costs in plain terms.
3. **Ops & access readiness.** These are the site owner's jobs, and they are the ones that ruin
   launch days. Read the `[human]` items out loud and get an answer for each.
4. **Not covered, verbatim.** Every line, unedited, introduced honestly: "here is what this did not
   check". Never summarise it, never call it minor, never leave it out because the list is long.

## The two checks that never run

Every report ends with these, and they are there because they are the two failures that hurt most
and that no crawl can ever reach:

- **Copy vs. source documents.** Nothing here compares the words on the site against the signed-off
  copy. Somebody has to sit with both and read.
- **Pages vs. agreed scope.** Nothing here knows which pages were supposed to exist. A page that
  was never built is invisible to a crawler.

Say both out loud when you present the report. A site can pass every check in this skill and still
be missing half of what was agreed.

## References

Read the file for a dimension before you explain its findings. Each one covers what the finding
means, why it matters at launch, how to fix it on common stacks, and what the check cannot tell
you.

| File | Covers |
|---|---|
| `references/reading-the-report.md` | Severities, the screenshot checklist, Not covered, presenting to a client |
| `references/indexability.md` | Crawl and inventory, noindex, robots.txt, sitemaps, canonicals, hreflang |
| `references/host.md` | HTTPS, certificates, www vs apex, redirects, security headers, the 404 page |
| `references/head.md` | Titles, descriptions, headings, icons, social cards, structured data |
| `references/links.md` | Broken and unverifiable links, link text, `mailto:` and `tel:` |
| `references/images.md` | Alt text, dimensions, loading strategy, weight, formats, video |
| `references/forms.md` | The inventory, endpoints, classification, and the test submission |
| `references/accessibility.md` | The HTML floor, axe violations, and the fifteen-minute manual pass |
| `references/performance.md` | Hints vs. measurements, Lighthouse, and ordering the work |
| `references/analytics.md` | Tag detection, firing, consent, and the verification pass |
| `references/content.md` | Placeholders, stale dates, contact detail variants |
| `references/redirects.md` | The cutover map, `redirects.csv`, and writing the rules |
| `references/ops.md` | Email authentication, legal pages, and the readiness checklist |

## Where this sits

`pre-launch` is the gate that runs against the repository before deploy. `launch-audit` is this
one: it reports and never blocks. `post-launch` runs the moment DNS moves and diffs production
against the baseline this audit wrote. Run them in that order.
