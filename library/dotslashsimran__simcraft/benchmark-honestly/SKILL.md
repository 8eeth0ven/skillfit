---
name: benchmark-honestly
description: Build benchmarks that survive scrutiny and catch the classic lies (dead code elimination, lazy results, constant folding, warm caches, coordinated omission, averages hiding GC pauses, unequal work, noisy machines). Defines the question first, controls and discloses the environment, uses warmups, interleaved repeats, medians, bootstrap confidence intervals and Mann-Whitney tests, and ends with a one-line verdict that includes the CI. Bundles a command runner, an environment reporter and an open-loop latency tester. Use when the user says "benchmark this", "is this faster", "compare performance", "did my change speed it up", "load test", "latency percentiles", "p99", or posts a speedup claim to check.
---

# Benchmark honestly

A benchmark is a claim: "under these conditions, A takes this long, and B is this much faster, give or take this much". Most published benchmark numbers are wrong because one of those parts is missing. This skill makes every part explicit and runs checks that catch the usual mistakes. Deeper explanations are in `reference.md`.

Scripts live in `~/simcraft/skills/coding/benchmark-honestly/scripts/`. They need only Python 3.9+.

## 1. Write the question down first

Before running anything, agree on these with the user and write them at the top of the report:
- **What is measured:** throughput (work per second) or latency (time per request). For latency, **which percentile** matters (p50 for typical, p99 or p99.9 for the tail users complain about).
- **Cold or warm:** first run after start (caches empty, JIT not compiled) or steady state. These are different questions with different answers.
- **The workload:** realistic input sizes and shapes. A 100-element input fits in L1 cache and says nothing about a 10 GB one.
- **What difference matters:** "a 2% gain is worth shipping" or "only 20% matters". Pass it as `--min-effect`.
- **Microbenchmark or end to end:** a 3x faster function inside a request that spends 95% of its time on the network changes nothing. Measure end to end before celebrating a micro result.

## 2. Pick the tool

Use the ecosystem's own tool if it is installed, because it runs in-process with less overhead:

| Ecosystem | Tool | Compare two versions with |
|---|---|---|
| Any command | `hyperfine --warmup 3 -N 'a' 'b'` | its relative output, or `bench.py` for CIs |
| Python | `pyperf` (or `pytest-benchmark`) | `pyperf compare_to old.json new.json` |
| JS / TS | `mitata` or `tinybench` | run both in one file |
| Go | `go test -bench . -count 20` | `benchstat old.txt new.txt` |
| Rust | `criterion` | `--save-baseline` then `--baseline` |

Otherwise, or to get the statistics and the checks, use the bundled runner:

```
python3 scripts/bench.py -n old -n new "python3 old.py" "python3 new.py" \
  --runs 30 --warmup 3 --floor "python3 -c pass" --same-output \
  --md report.md --json report.json --chart chart.svg --redact
```

The first command is the baseline. It runs warmups, then shuffled rounds so drift hits every variant equally, records wall time, CPU time and peak memory, and prints medians, bootstrap CIs, a Mann-Whitney test, Cliff's delta and a verdict. `--floor` takes an empty version of the program (same startup, no work) and flags any variant that is not clearly slower than it. `--same-output` flags variants that print different results. `--prepare CMD` runs before every timed run (for example to evict a cache). `--subtract-floor` compares the work alone, without startup.

For latency under load, use the open-loop tester, never a loop that waits for each reply before sending the next:

```
python3 scripts/latency_test.py --url http://127.0.0.1:8080/ --rate 200 --duration 30 --md latency.md
```

## 3. Control the environment, then disclose it

Run `python3 scripts/env_report.py --redact` before and after (bench.py includes it automatically). Fix what it warns about: plug in the laptop, turn off low power mode, close busy apps, on Linux set the governor to performance and pin with `taskset`. On macOS you cannot pin cores or turn off turbo, and Apple Silicon may put the run on slow efficiency cores; say so in the report. Check that you are timing a release build (`-O2`, `--release`, `NODE_ENV=production`), not a debug build.

## 4. Check for the lies

Go through the list in `reference.md` ("The lies") for the code at hand. The short version:
- Is the result used? (dead code, lazy iterators, constant folding). Print or return a checksum.
- Is every variant doing the same work on the same input? Compare outputs.
- Did the previous run warm a cache for the next one? Shuffle the order, and say if the numbers are warm or cold.
- Is the work bigger than the timer and startup cost? Compare against the floor.
- Is latency measured from the intended send time? Is the tail reported, not just the mean?

## 5. Report

Every report has: the question, a chart showing every run (not just a bar), the setup table, the exact command to reproduce, and one honest line, for example "new is 1.18x faster than old (95% CI 1.09x to 1.27x, 30 runs each, warm cache, M2 laptop on AC power)". If the CI includes 1.0, the line says there is no clear difference. Never report a speedup from a single run or from means alone.

## Examples

`examples/` has four real cases run on a busy laptop, each with the naive result next to the honest one: a lazy `map()` that looks 100,000x faster, two identical sorts where single runs give a different "winner" each time, a file read where whichever variant runs first loses, and a server with GC-like pauses whose p99 looks fine in a closed loop. See `examples/README.md`.
