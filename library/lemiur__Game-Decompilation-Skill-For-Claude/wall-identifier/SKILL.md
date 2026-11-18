---
name: wall-identifier
description: Classify a matching-decompilation wall before spending effort on it. When a reconstruction plateaus below 100% and no spelling obviously closes it, name which compiler decision diverged (inline/call set, control flow, register/schedule, or masked/referent) and route to the lever for that class. Use when a function is stuck, when triaging plateaus, or when asked "why won't this match". Complements matcher (reconstructs) and permute (breaks proven codegen residue); this one diagnoses.
---

# wall-identifier: classify the wall before fighting it

Project guide: the repository's `AGENTS.md`. If the repository has none, use [AGENTS-template.md](../matcher/references/AGENTS-template.md) and ask the user to fill in its project adapter.

A pinned compiler is deterministic: `bytes = f(preprocessed unit, flags)`. Retail came out of the same `f` from
real source, so every function can be reproduced in principle; the job is finding which *input* differs. The unit
of reproduction is the whole translation unit, because some residue is front-end state that no local edit to the
body can reach. Each class below has a different lever, and two of the four are not permuter problems at all.

## Start here

Using the project's tools (see the `AGENTS.md` adapter):
- **Diff:** the normalised compiled and retail pair, with the first divergence, call, branch and return counts,
  and both sides' leading instructions;
- **Semantics:** an operand, FP-opcode, constant and ordered-referent comparison;
- **Switches:** jump-table case-to-arm mapping against retail (a permuted table scores near-exact);
- **Headroom:** current versus best-ever score;
- **Blocks:** a basic-block view of retail;
- **Referents:** the actual relocation targets, unmasked.

## The four classes, in routing order

Do not call a wall class N while class N-1 still diverges.

| class | deciding signal | lever |
|---|---|---|
| **inline / call set** | the out-of-line CALL multiset differs | body completeness, inline boundary, or a duplicated call tail |
| **control flow** | block, branch or return counts differ | a source construct: structural matcher work |
| **register / schedule** | counts and branch sequence agree; operand order, spills or colouring differ | the source-shape checklist, then the permuter |
| **masked / referent** | masked diff identical but score below 100 | referent identity: labelling work, not codegen |

### Inline / call set

Know the compiler's inline policy first, and record it in the project notes:
- what `/O2` implies (for example `/Ob1` on older MSVC: unmarked non-template functions stay calls);
- whether template members expand without `inline`;
- how the per-caller budget works, and whether it has cliffs.

- The class is **inline/call set**, not "inline budget". A call-count delta can also be a duplicated or merged exit
  tail that carries a call, and an equal-count callee substitution can be a wrong identity. Name the differing sites
  before choosing a lever.
- A callee present on both sides with different counts does not distinguish a per-site inline decision from a
  cross-jumped call tail. Locate the sites and check retail's jumps first.
- A missing expansion usually means the *caller's* body is incomplete, because the budget follows statement mass.
  Finish the caller before touching the callee.
- Check which objects emit a COMDAT for the helper (`dumpbin /symbols`, `llvm-nm`).
- Never land a forcing device (a member-function-pointer reference, `dllexport`, an artificial caller) to
  materialise a COMDAT.

### Control flow

A count mismatch is a reconstruction problem. Tail-merging has distinct regimes chosen by the source:
- separate returns;
- `goto fail` to one exit;
- total `||`/`&&` collapse;
- loop forms (`while` versus `do/while`, backward gotos).

See the matcher lever catalogue, sections 6 and 7.

One narrow exception exists. Suppose the first real divergence is an earlier register rotation, and every extra
edge is confined to the returns of an inlined value-only accessor. Register availability can then decide whether
the optimiser factors the caller's tail, giving a branch or return-count delta downstream of colouring with no
authored CFG difference.

Require the complete signature:
- same guards, call set, constants and ordered referents;
- only the accessor-return tail differs;
- source-shaped controls are byte-flat.

This is not permission to relabel an ordinary branch mismatch from counts alone: follow the first divergence.

### Register / schedule

Reached by elimination only.
1. Exhaust the source-shape checklist (the matcher's `references/levers.md`): widths, cv/ref boundaries, local
   census and lifetimes, helper boundaries, statement grouping. One misplaced register operation can mean the
   *type* is wrong, for example a member array modelled as scalars, or a lost aggregate.
2. Then use the permuter (`permute` skill).

Unit-global effects exist: a flat probe sweep is evidence about the probe, not about the function. Probes are
diagnostics: bank the result, then delete them.

### Masked / referent

Relocation scoring is strict: the target name or address, the pointed-to data, and DIR32 addends all count. By
construction, a masked diff cannot show a wrong callee. If the masked bodies agree while the score sits below 100,
audit the actual referents, fix the labelling or identity model, and do not permute.

## Transferring doctrine between compilers

Mechanisms proven on one compiler (for example the VC6 register-allocator model, `/Ob2` semantics, budget
cliffs) are hypotheses on another until re-proved there with A/B evidence. Keep compiler-specific findings in the
project's pattern notes, labelled with the compiler build they were proved on.

A reproducibly bounded residue stays visible through the score ledger and a valid early-stop note, never through a
hand-kept list of walls. Add a reusable lever to the pattern notes only with bounded A/B evidence.
