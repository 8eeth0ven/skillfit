---
name: suggest-improvements
description: List what is worth fixing on a site the conversion reproduced as-is — SEO, content, links, accessibility, performance, security, analytics and design — each item with its path, evidence, effort, risk and whether it can be applied mechanically, plus the agent's own design and content observations. Use after the parity gates and the visual review are green and before the pull request, or when someone asks what could be better on the converted site. It changes nothing.
---

# suggest-improvements

The converted site reproduces the live site on purpose, flaws included. This skill writes down
the flaws, with evidence, so the site owner can decide which to fix. It never fixes them.

## The golden rule

**Nothing from here is applied directly.** An improvement becomes a proposal: an entry in
`proposals.json` that ships only in a `PROPOSALS=on` build until a person approves it, or a later
`convert-site --apply <id>` run that does the same on its own commit. Editing the default build
because this report said so breaks parity, and the gates will say so.

## When to run

After every parity gate passes and the visual review is green for every page, with `review/`
still on disk (it feeds the design checks), and before the pull request is opened. The report
goes in the PR.

## The command

From the site root:

    node <skill-dir>/scripts/suggest.mjs --capture capture --baseline baseline --review review --out docs/suggestions.md --json suggestions.json

Add `--gates gates.json` when the gate runner wrote that file (the header then summarises the
gates), and `--lighthouse capture/lighthouse-live` when that folder exists (it is also the
default). Run `node <skill-dir>/scripts/suggest.mjs --help` for every option.

Exit 0 means the report was written, whatever it found; 2 is a usage error or a missing input.
It reads `capture/`, `baseline/` and `review/` only and never requests the live site.

## Reading the report

`docs/suggestions.md` opens with the site, the counts and the gates line, then the
**Not covered** list, then one section per category: SEO, Content, Links, Accessibility,
Performance, Security, Analytics, Design. Inside each, one heading per check with its reason,
then one line per item:

    - `/about/` `h1` (`missing-h1`, effort S, risk low)
      - Evidence: no <h1> on the page

- **Path** is the page (for a site-wide problem, the first page it appears on).
- **Effort** is S, M or L; **risk** is none, low, medium or high; **applyable** means
  `convert-site --apply <id>` can make the change mechanically.
- **Evidence** is what the check saw in the capture: a value, a count, the pages.
- **Grouped items.** One problem repeated across the site (a script in the header, an image, a
  link, a title) is one item, not one per page. The evidence names the page count and the first
  three pages; `pages` in `suggestions.json` lists every page it applies to. Use the JSON when
  you need the full list.
- The report ends with **How to apply**, listing the checks that can be applied mechanically.

**Not covered is never a pass.** A check with no input (no `--review`, no Lighthouse reports, no
`media.json`) is listed there, and so is part of one. A check that threw is listed as
`check failed: <message>`; a check whose coverage note threw keeps its items and is listed as
`(partly): coverage note failed: <message>`. The other checks still ran. Quote the whole Not covered list verbatim in the PR, unedited. If
`--review` was missing because `review/` was deleted, rerun the visual review's shoot and styles
steps and run this again rather than shipping the gap.

## What you add by hand

The scripts cannot see everything. At the end of `docs/suggestions.md`, add a section:

    ## From the review

    - `/services/` hero: the heading overlaps the image at 390 px on live and new alike
      - Evidence: review/index.html, pair /services/ at 390, top of page

What goes there:

1. **Design observations from the contact sheet**: anything that looks wrong on live and was
   reproduced faithfully (cramped spacing, an image cropped badly on mobile, low contrast, a
   misaligned grid). Name the route and width.
2. **Content issues noticed while building**: typos, outdated copy, dead offers, a phone number
   that differs between pages, a page that duplicates another. Quote the text and name the
   captured file it came from.

Each line carries the same discipline as the script's items: a path, evidence a person can check
(a route and width on the contact sheet, a file under `capture/`, a quoted snippet), and nothing
you did not see. No guesses, no "probably". If the list is empty, write "Nothing further noticed."
so the reader knows you looked.

Do not rerun the script after adding the section: it rewrites `docs/suggestions.md`. Rerun it
first if the inputs changed, then add the section again.

## Acting on an item

Never in this run. When the person picks an item:

- **Applyable checks**: `convert-site --apply <id>` records the proposal in `proposals.json`,
  makes the change on its own commit, reruns the gates and the contact sheet, and ships it only
  with `PROPOSALS=on`.
- **Everything else** (alt text, copy, which duplicate page to keep, a design fix): a person
  decides or writes it, and it goes in as a proposal the same way, never into the default build.

## The checks

`references/catalogue.md` lists every check: its id, category, what it looks for, the evidence it
cites, its default effort and risk, whether it is applyable, which checks group across pages, and
which inputs each check needs. Read it when an item's reason is unclear or a check is missing
from the report.

## Present the result

1. **The counts per category**, then the items with risk medium or high and the applyable ones.
2. **From the review**, every line.
3. **Not covered, verbatim**: every line of the report's list, unedited. None of it was checked.
4. **What happens next**: nothing is applied until the person picks items; each becomes a
   proposal or a `--apply` run.

## References

| File | Covers |
|---|---|
| `references/catalogue.md` | Every check, its evidence, effort, risk, applyability and inputs |
