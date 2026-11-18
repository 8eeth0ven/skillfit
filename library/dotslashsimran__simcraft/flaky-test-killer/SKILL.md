---
name: flaky-test-killer
description: Find why a test is flaky and fix the root cause, never by adding retries, sleeps or bigger timeouts. Measures the flake rate with a confidence interval, runs the test under stressors (random order, timezone, fake clock at month end or DST, CPU load, fresh temp dir, low file limits), bisects for the test that pollutes it, and proves the fix with before and after numbers. Use when the user says "flaky test", "test passes locally fails in CI", "intermittent failure", "random test failure", "works on my machine", "test fails sometimes", "only fails in the full suite", or wants to quarantine or retry a test.
---

# Flaky test killer

A flaky test is a real bug: in the test, in the code, or in the environment. Retries hide it, and the same bug will later show up in production or in another test. The job is to make the failure happen on demand, name the cause, fix it, and prove with numbers that it is gone.

Scripts are Python 3.9+ standard library only. `S=~/simcraft/skills/coding/flaky-test-killer/scripts`.

## Rules

- **No retries, no sleeps, no longer timeouts, no `skip`** as the fix. A wait is fine only when it waits for the actual condition (an event, a join, a poll with a deadline).
- **Measure before you change anything.** Without a "before" rate you cannot prove an "after".
- **One cause at a time.** Many flaky tests have two bugs. Fix one, measure, and look again.
- **Keep an evidence log** (see below). Every claim needs a command and a number.

## Steps

1. **Reproduce and measure.** Run the single test, then the whole suite, many times.
   ```
   python3 $S/flake_rate.py -n 50 --json before.json -- <test command>
   python3 $S/flake_rate.py -n 200 -j 8 --json before.json -- <suite command with shuffle seed {seed}>
   ```
   It prints the failure rate with a 95% Wilson interval, groups distinct failure messages, counts failures per test name, compares pass and fail durations, and gives cause hints. `{seed}` becomes a new random seed every run, and failing seeds are printed so you can replay the exact order. `--until-fail` stops at the first failure and shows the output. If the rate is 0 after 50 runs, go to step 2: the trigger is something your machine does not do.

2. **Run alone vs in the suite vs in parallel.** Fails only in the suite means order or shared state (go to step 4). Fails only with `-j` means a shared resource such as a port, file or database. Fails alone means time, randomness, a race, or the environment.

3. **Sweep the stressors** to see which one moves the rate:
   ```
   python3 $S/stress.py --sweep -k 5 -- <test command>
   ```
   It runs a baseline and then each stressor on its own: five timezones, nine fake clocks (midnight, month end, Feb 28, leap day, year end, both DST switches, 2038), heavy CPU load, a fresh temp dir, a low open-files limit and a Turkish locale. A stressor is flagged only when a Fisher exact test says it really changed the rate. If the baseline always fails, it tells you which setting makes it pass (say `tz=UTC`, the classic "passes in CI, fails locally") and which settings make it fail with a different message (a second, hidden bug). Pin the first cause and sweep again: `stress.py --sweep --tz UTC --only clock -- ...`. Use the same flags without `--sweep` for a single stressed run.

4. **Find the polluter** when the test passes alone but fails after others. Save the order of a failing run (the test ids that ran before the victim, in order) and bisect:
   ```
   python3 $S/find_polluter.py --tests order.txt --victim <id> --cmd "<runner> {tests}" [--fail-pattern "<victim's failure text>"] [--repeat 3]
   ```
   It checks the victim passes alone and fails after the list, then shrinks the list with delta debugging to the one test (or smallest group) that breaks it. If the victim fails alone and passes after the list, it finds the "state setter" the victim secretly depends on. Use `--fail-pattern` so another flaky test in the list does not confuse the search.

5. **Name the cause and fix it at the root.** Look up the failure signature in the cause table in [reference.md](reference.md). Each row gives the signature, the stressor that exposes it, and the right fix.

6. **Prove it.** Run the same command again with enough runs and compare:
   ```
   python3 $S/flake_rate.py -n 300 -j 8 --json after.json --compare before.json -- <same command>
   python3 $S/flake_rate.py --plan 0.01     # clean runs needed to claim rate < 1%
   ```
   "Fixed" means the Fisher test says the drop is real AND the stressor that exposed the bug now passes. To claim a rate below X with 95% confidence you need about 3/X clean runs in a row (299 for 1%). Ten green runs prove almost nothing for a 5% flake.

## Evidence log

Keep a short log in the PR or issue, one line per step:
```
before: 42/60 failed (70%, CI 57-80%) cmd: run_tests.py --seed {seed}
cause 1: polluter tests.test_users...test_enable_eu leaves SETTINGS["symbol"]="€" (find_polluter, 7 probes)
cause 2: test_export sleeps 10ms, worker takes 0-20ms (fails alone, rate 60%, not moved by any stressor)
fix: patch.dict around the polluter; victim sets its own state; worker returns an Event, test waits on it
after: 0/300 failed (rate < 1.0% at 95%), Fisher p = 7e-41; sweep clean on tz, clock, cpu
```

## Practise

`python3 ~/simcraft/skills/coding/flaky-test-killer/examples/make_examples.py --out /some/tmp/dir` makes a unittest project and a node:test project with an order dependency, a month end bug, a timezone bug, a sleep race and an unawaited promise. `--variant fixed` writes the fixed versions to compare against.

Per-ecosystem commands (pytest, jest, vitest, node:test, go, cargo, JUnit), the full cause taxonomy, and the statistics are in [reference.md](reference.md).
