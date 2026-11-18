---
name: system-design-from-scratch
description: Design a backend or distributed system by building a tiny but real working version of it, proving its properties with invariant tests, a load test (throughput and p50/p95/p99 latency) and fault injection (crashed nodes, dropped or delayed messages, partitions, clock skew, full disks), then writing a design doc with the numbers, alternatives, where it breaks, how Redis, Kafka, Cassandra or etcd do it, and an interview-ready summary. Works for rate limiters, job queues with retries and visibility timeouts, consistent hashing, LSM-tree key-value stores, write-ahead logs, Raft leader election, caches with eviction policies, pub/sub, URL shorteners and similar. Use when the user says "build a rate limiter from scratch", "system design practice", "how does Raft work, let's build it", "design X and prove it", "load test my design", "what happens to X when a node dies", or is preparing for a system design interview and wants more than boxes and arrows.
---

# System design from scratch

A whiteboard design is a guess. This skill turns it into evidence: a small system that actually runs, tests that state what must always be true, a load test that measures it, and faults that try to break it. The design doc at the end only contains claims that something in the folder proved.

The sibling skill `from-scratch` teaches one concept step by step. This skill is for systems with load, failure and trade-offs. Use `from-scratch` first if the user has never seen the core idea.

## Tools in this skill

- `scripts/loadgen.py`: async load generator for a Python function or an HTTP endpoint. Open loop (`--rate`, fixed schedule, latency counted from the scheduled time) or closed loop (`--concurrency`). Reports throughput, outcome counts and p50/p90/p95/p99/p99.9 from HdrHistogram-style buckets, plus the generator's own lag. `--rates 200,400,800` sweeps load to find the knee. Text chart always, PNG with `--plot` if matplotlib is installed.
- `scripts/faultsim.py`: deterministic discrete event simulator for message passing nodes. Delay, drop, duplicate, partition, one-way block, crash and restart (disk survives), clock offset and drift, disk full, a random fault schedule (`random_faults`), and invariants checked after every event. Same seed, same run. `python3 scripts/faultsim.py --demo` shows the basics.
- `examples/rate-limiter/` and `examples/raft-election/`: two complete runs of this workflow, each with a `DESIGN.md` of real results. Read the matching one before starting a similar system.

Check what is installed first: `python3 --version`, `go version`, `python3 -c "import matplotlib"`. Default to Python 3.9+ standard library. Use Go only if it is installed and the user wants it (the scripts still work against a Go server over HTTP).

## Workflow

Do the steps in order. Show the user each step's output before moving on, and ask one question at a time when something is unclear.

1. **Requirements and numbers.** Write a short table: what the system does, scale (QPS, keys, data size), latency budget, durability and consistency needs, and what happens on failure. Then do the back-of-envelope math out loud: memory per item times items, requests per second per node, round trips per request, disk bytes per day. Note which numbers already rule a design out. Patterns and reference figures are in [reference.md](reference.md#1-numbers).

2. **Smallest correct version.** One file per component, plain Python. Make time injectable (a `clock` parameter or a faultsim node) so tests can control it. For anything with more than one node, build it as `faultsim.Node` subclasses first; only add real sockets for the load test. Leave out everything not needed to show the core trade-off, and list what was left out.

3. **Invariants and property tests.** Write down what must always be true (for example "never more than burst + rate x T admitted", "at most one leader per term", "a read after an acknowledged write returns it"). Test each over hundreds of seeded random inputs, compare against a brute force oracle where one exists, and keep one test per known weakness that shows it on purpose. [reference.md](reference.md#3-invariants-by-system) lists invariants for each common system.

4. **Load test.** Use `loadgen.py`. Prefer open loop for latency claims; closed loop hides queueing (coordinated omission). Sweep offered load to find where latency bends. Always look at the generator lag line: if it is high, the numbers describe the laptop, not the system. Say so in the doc.

5. **Fault injection.** In faultsim: crash the leader or a replica, partition minority from majority, drop 10 to 30% of messages, slow one link, skew or speed up one clock, fill one disk. Then run `random_faults` across 100+ seeds with invariants on. Plant one realistic bug (skip an fsync, forget a check) and confirm the tests catch it; if they do not, the nemesis or the invariant is too weak. Keep every failing seed as a regression test.

6. **Design doc.** Write `DESIGN.md` next to the code with these sections: requirements and numbers; what was built; invariants and test results; load results; fault results; the decision; where it breaks; what production systems do differently (cite their public docs, see [reference.md](reference.md#4-what-production-systems-do)); a five sentence interview summary that uses the measured numbers; and the commands to reproduce. Every number in it must come from a run in this session. Mark machine-dependent numbers with the machine's load.

## Rules

- Never write a result you did not get. Never round a bad number into a good one.
- Simulated time for correctness and distributed behaviour; real time only for cost and throughput, and report how busy the machine was.
- A test that has never failed proves little. Show each invariant failing at least once (a planted bug or a removed check).
- "0 failures in N seeds" means the failure rate is probably below about 3/N, not zero. Say that.
- Compare at least two designs on the same workload. The trade-off is the point.
- When citing a production system, describe only what its public docs or papers say.
