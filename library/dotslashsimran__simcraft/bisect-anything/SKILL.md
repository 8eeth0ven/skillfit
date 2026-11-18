---
name: bisect-anything
description: Find the exact commit (or dependency version, config value, or input) that caused a regression by turning it into an automatic pass/fail check and running git bisect run in a separate worktree, then shrink the bad commit to the hunk that matters and explain it. Handles failing tests, changed output, slowdowns, crashes, visual changes, server behaviour, flaky checks, unbuildable commits and merge-heavy history. Use when the user says "what broke this", "find the commit that", "when did this start", "it used to work", "regression", "git bisect", "which version broke it", or "which change made it slow".
---

# Bisect anything

A bisect is only as good as its oracle: the command that says "good" or "bad" for one commit. Almost every wrong bisect answer comes from an oracle that is flaky, tests the wrong thing, or calls a broken build "bad". So spend most of the effort on the oracle, prove it on both ends, and let the scripts do the rest.

Scripts are in `~/simcraft/skills/coding/bisect-anything/scripts/` (Python 3.9+, standard library only). Details, recipes and pitfalls are in `reference.md` next to this file.

## 1. Pin down the regression

Ask only for what is missing, one question at a time:
- **What is wrong**, as something a command can check (a failing test, a wrong number, a slow page, a crash, a changed screenshot).
- **A good point**: a tag, release, date or commit where it worked. If nobody knows, try an old tag; checking one old commit is cheap.
- **The bad point**: usually `HEAD`.
- **How to build and install** at an old commit.

## 2. Write the oracle

Exit `0` good, `125` cannot test this commit, any other code bad. Keep the oracle script **outside the repo** (or pass it with `--overlay`), because old commits do not have it. Pick the recipe that fits; full versions are in `reference.md`:

| Regression | Oracle |
|---|---|
| A test fails | run that one test only, with `--overlay` if the test is new |
| Output changed | `oracles/golden_oracle.py`, with `--ignore` for times, versions and ids |
| Got slower | `oracles/bench_oracle.py`: measure both ends first, threshold between the medians |
| Crash | exit 1 only for the crash signature (signal or message), 0 otherwise |
| Looks different | render a screenshot, then `oracles/img_diff.py` with a tolerance and masks |
| Server behaviour | `oracles/serve_oracle.py`: free port, wait until ready, probe, always kill |

Narrow the oracle to this one bug. "The whole test suite passes" finds the first commit that broke anything, which is rarely the one the user cares about.

## 3. Run it

```
python3 scripts/bisect.py --good v2.3.0 --bad HEAD \
  --install "npm ci" --build "npm run build" \
  --oracle "node /path/outside/repo/repro.js" --repeats 3 --timeout 120
```

It works in a separate worktree, so the user's checkout and uncommitted work are untouched. It first checks the oracle says good on `--good` and bad on `--bad`, and stops if not. Install runs only when a lockfile or manifest changes; a failed install or build marks the commit as skip (125).

Choose flags with judgement:
- Flaky oracle: `--repeats 5` (majority vote). A bug that only shows sometimes: `--repeats 10 --vote any-bad`.
- Hangs: `--timeout`; a timeout counts as bad unless `--timeout-means skip`.
- Merge-heavy history, or "which PR broke it": `--first-parent`, then bisect inside the merge it names.
- Stale build output fools you: `--clean --keep node_modules`.
- Looking for the fix instead: `--find-fix`.

For things that are not commits (package versions, nightly builds, config values, data rows), use `scripts/bisect_list.py` over an ordered list, or `--minimise` to find the smallest set of flags or inputs that still fails.

## 4. Explain the commit

1. Read the found commit with `git show`. If the report says "not conclusive", the answer is one of the listed commits next to a skipped one. Say so honestly, do not pick one.
2. Shrink it: `scripts/hunk_minimise.py --commit <sha> --oracle ... --build ...` finds the smallest set of hunks that still causes the problem.
3. Tell the user, in plain words: the commit (hash, title, author, date), the exact hunk, **why** that change causes the symptom, and how sure you are (steps, skips, repeats). Suggest a fix or a revert, and a regression test built from the oracle.

## Check your work

Run `python3 examples/selftest.py`. It builds a 40-commit demo repo with a planted bug, slowdown, visual change and unbuildable commits, and checks that every scenario finds the right commit (about one minute).
