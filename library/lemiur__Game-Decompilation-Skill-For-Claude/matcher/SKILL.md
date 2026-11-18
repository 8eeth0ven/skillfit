---
name: matcher
description: Reconstruct and byte-match C/C++ functions, translation units, classes, globals and referents against a retail binary with the original compiler, writing source that passes the decomp-code-rules reader test (no fakematches). Use for function matching, lost-match recovery, unit reconstruction, class/type/vtable/calling-convention recovery, relocation and referent correction, data modelling, finishing a matched function to the code rules, and diagnosing a plateau before declaring it bounded or reaching for a permuter.
---

# matcher: reconstruct, then compare

Project guide: the repository's `AGENTS.md`. If the repository has none, use [AGENTS-template.md](references/AGENTS-template.md) and ask the user to fill in its project adapter.

Recover the source structure that explains retail's bytes. `AGENTS.md` holds:
- the authority;
- the modelling rules;
- the project adapter, with its generic verbs: `build`, `match`, `diff`, `disasm`, `xref`, `class`, `gate`,
  `rules`;
- the code-rules profile: dialect, naming and layout style per module, and evidence sources.

This skill is the working loop. Use the other skills for these:
- **`decomp-code-rules`:** the rules every line you write must follow, and what counts as a match.
- **`wall-identifier`:** classify a plateau.
- **`helper-recovery`:** open-coded helpers.
- **`permute`:** only a diagnosed register/schedule residue.

**The goal is source a reader can understand.** Identical bytes prove that the source is faithful. A match counts
only when the source also passes the [match] code rules and the reader test:

> Would a programmer on the original team have typed this?

Write to the rules while reconstructing, not afterwards. Code that matches through a trick (a dummy local,
`volatile`, an empty block, an offset cast, a reused variable) is a **fakematch**. It is not a closure: it is
evidence about where the real source differs (`decomp-code-rules`, Section F).

Do not write per-function plan files unless asked. A brief note of the target, the hypothesis and the next
compiler control is enough.

## Choose work

- Work the never-matched and lowest-scoring functions first, or recover lost matches (historical best above
  current best).
- **`MATCH-PENDING` functions** are byte-exact but fail a [match] rule, usually a fakematch. They are open work,
  ranked like a high-scoring function: the bytes are known, and the source isn't.
- Do not revisit a function that is already exact and passes the rule checker. Do not investigate a current-score
  dip in an unchanged function; the gate decides regressions.
- Before inventing a spelling, look for an existing verdict: source comments, the stub marker's note, review
  ledgers, history.

## Evidence pass (before editing)

Gather, using the project's tools:
- **The gap:** where the first divergence is, with both sides' assembly.
- **Operands:** operand, constant, FP-opcode and *ordered relocation-target* differences.
- **Switch tables:** if there is a switch, its case-to-arm mapping against retail's tables.
- **Retail assembly**, read directly. Decompiler output is a hint about structure, never source. Its variable
  merges, casts and placeholder names are what the rules exist to remove.
- **Context:** callers and callees, vtable slots, the class hierarchy and RTTI.
- **Naming evidence** (`decomp-code-rules` R7), which the binary often carries itself:
  - error and log strings that start with a function name (`"FS_Read: ..."`);
  - console-variable and command strings;
  - assert text, exports, RTTI and symbol files.
- **Local style:** the module's row in the profile's style table, and the already-finished functions in the same
  unit. New code follows that style (R8), not a project-wide default.

Also read the whole source function, its declaration, callers and callees, adjacent family members, the class
layout, and any surviving or lineage source. Resolve identity and layout doubts before calling anything codegen
residue. Mine history every time:

```sh
git log -S'<function-name>' -- src include
git log -G'<mangled-name>' -- <score ledger>
```

For a lost match, recover the exact source revision that matched before inventing new forms.

## Reconstruct, then compare

Rank hypotheses by evidence:

1. surviving or source-oracle bodies, and the complete function family;
2. defects in identity, ABI, ownership, type, layout or referent, or a missing body;
3. authentic inline, helper, macro, operator and constructor boundaries;
4. local census, scope, lifetime, initialisation, parameter reuse, and statement and control-flow shape;
5. expression shape, loops, library idioms, evaluation order;
6. compiler-state experiments, only after semantics, call set, CFG, constants and referents are credible.

Every candidate is written as the original programmer would have written it:
- typed members, not offsets (R4);
- one local per meaning, named for it (R30);
- named constants (R11): in C, `#define` or enum, since a `const int` is an object;
- the era's own idioms where the bytes need them (R35): `*p++`, `goto fail`, an assignment in a search loop.

A candidate that works only through a Section F form is not an answer. Read it as a pointer:
- a dummy local that fixes allocation points to a missing helper or a merged variable (R16, R30);
- `volatile` points to a wrong type or an aliasing pointer;
- an empty block or a `do { } while ( 0 )` points to a macro;
- a same-type cast points to a wrong declared type.

Follow the pointer to the source that explains it.

**Inline helpers:**
- A missing out-of-line copy is not evidence against an inline helper. Trivial accessors are always expanded
  and leave no out-of-line copy in retail.
- Retail's bytes cannot distinguish `World()->Sounds()` from `m_world->m_sounds`, yet the inline sites change
  the caller's inline budget.
- When budget measurements say sites are missing, adopt the repeated accessor spellings that supply them, at
  every site in the tree.

[references/levers.md](references/levers.md) catalogues the levers that have produced exact closures. Scan it so
the search is not limited to the first familiar explanation.

**For each candidate:**
1. Name the source change and the emitted delta you expect.
2. Run `match <unit>`.
3. Compare from the first real divergence: instructions, constants, call and CFG structure, ordered relocations.
   A fuzzy score alone is insufficient.
4. Do not reject a sourced or structurally convergent base on a single dip. First confirm that the feature you
   are chasing was absent from the baseline.

"Checked" means a real A/B was compiled in the real unit, or retail or source evidence proves the form
inapplicable. Do not mix independent levers in one experiment, and do not retain probes, unused declarations,
artificial locals or distorted source.

## Recover lifetimes (do this alongside inline helpers)

Before treating stack or register differences as compiler-state residue, recover the ownership and lifetime of
each value around the first divergence. Read the caller and its expanded helpers together: named locals,
parameters, references, returned aggregates and unnamed temporaries all feed the caller's allocation.

1. **Map stack accesses to real values**, accounting for pushes. Distinguish:
   - an aggregate home;
   - a scalar spill;
   - a reused argument slot;
   - a hidden return buffer.

   A frame-size difference alone does not identify the cause.
2. **Trace each value** from creation to last use, across calls and branches. Check declaration versus
   assignment, sibling versus nested scopes, and whether storage belongs to the caller or to an inline helper.
3. **Check full-expression boundaries.** Passing a returned aggregate directly, naming a copy, and binding a
   const reference give its temporary different lifetimes. Two expansions of one helper can get separate homes.
4. **Check parameter and result boundaries.**
   - By-value arguments are evaluated before the helper body, while references can defer loads to their uses.
   - A returned aggregate, a void output helper, and a helper returning a reference to caller-owned output are
     separate controls; test them as separate A/Bs.
   - A named callback pointer can change register allocation with the final call unchanged.
5. **Compare** emitted loads, stores, stack slots and call/branch structure.
   - A shorter lexical scope does not guarantee slot reuse.
   - Reusing one aggregate may shrink the frame but lose retail's load reuse.
   - Compose the next justified lever rather than judging by frame size or fuzzy score.

Use meaningful ownership and natural scopes, never dummy locals or arbitrary blocks to force allocation (R17,
R30). Record which lifetime controls were compiled before routing any residue to the permuter.

## Classify the plateau

Route in this order. Do not call a wall class N while class N-1 still diverges:

1. **Referent:** masked bytes identical, relocation targets differ. Fix the claim or identity.
2. **Inline/call set:** the multiset of out-of-line callees, or the ordered relocations, differ. The cause is an
   incomplete body, an inline boundary, or a duplicated call tail.
3. **CFG:** block, branch or return counts differ. This is structural source work.
4. **Register/schedule:** same calls and skeleton. Check widths, lifetimes and helper boundaries, then the
   permuter.

Details and proven exceptions are in `wall-identifier`.

## Model real entities

`AGENTS.md` "Source rules" and `decomp-code-rules` section A govern. In practice:
- **Casts are symptoms:** retype the member or the canonical class until placeholder casts disappear (R4, R19).
  Typed pointers replace `void *` past the boundary (R26).
- **Vtables:**
  - Recover them mechanically from vtable evidence: one vtable per polymorphic base.
  - Declare every real slot and no others. A slot of unknown purpose keeps a placeholder name (open naming
    work); never add dummy or padding virtuals (R13).
  - RTTI may be enabled per module, so missing RTTI does not prove a class non-polymorphic.
- **Structs:** one member per line with offsets of unknown members in their placeholder names. Comments carry
  units, owners and lifetimes (R27). Unknown ranges stay placeholder members named by offset, never invented
  names.
- **Calling conventions:** pin them from the disassembly (callee `ret N` versus caller `add esp,N`; `this` in
  ECX).
- **EH frames:** a destructible stack local forces an EH frame, and unwind states are evidence of the local
  census.
- **External callees** (engine, DirectX, Win32, COM) are declarations with no body, but their referents must
  still be the right names.
- **Data:** a datum is a real definition with its annotation. Compiler-generated payloads are recorded as such.
  Never model an interior address as independent storage, and never add source padding to fit a gap in the
  final image.

## Finish the source

When `match` reports exact:

1. **Commit the match at once,** before the next command that can touch the source.
2. **Run `rules <unit>`.**
   - A [match] finding makes the function `MATCH-PENDING`. Fix it now if the fix is clear, with `match` after
     each change.
   - If the fix isn't clear, the finding is a fakematch to report as an open wall, with the Section F row it
     fits. It is not a closure.
3. **Read the function once against the reader test** and Section F. Look for what the checker can't see:
   - a merged variable;
   - a confident invented name;
   - a missing helper behind a repeated expression;
   - a shipped bug that isn't labelled.
4. **Apply the [free] finishing rules** in their own commit:
   - the function's header banner (R33);
   - names from evidence (R7), invented names marked as invented, placeholders left where nothing is known;
   - named constants and flag groups (R11, R29);
   - braces and layout in the module's style (R8, R35);
   - comments on quirks (R36) and on `RULE-EXCEPTION`s.

   Then run `match <unit>` again. In a unit that embeds `__LINE__`, or when the binary carries line
   information, layout changes are [checked] (R23).
5. **[checked] cleanups** (a split variable, a restored helper, a retyped member) go one at a time, each with
   `match`. If one breaks the match, revert it, or keep the matching form with a `RULE-EXCEPTION` only if that
   form still passes the reader test.

A function that is exact but can't be finished in this batch is reported as `MATCH-PENDING` with its findings.
It is never reported as matched.

## Stop and hand off

- **The byte gate decides the bytes.** A function is banked only when the whole-binary gate (`AGENTS.md`, "The
  byte gate") prints green with it compiled from source; a per-function `MATCH` is the filter that feeds the
  gate.
- **The code rules decide whether it counts.** A byte-exact function counts as matched only when it also passes
  the [match] code rules (`AGENTS.md` "Code rules", the `decomp-code-rules` skill). These are:
  - one declaration per type and global;
  - no offset casts;
  - real vtables;
  - no fake code;
  - no assembly bodies.

  Report failures as `MATCH-PENDING`. A function the evidence shows was originally written in assembly is
  `ORIGINAL-ASM`, listed apart. Naming is not required.
- **Exact:** claim exact closure only from an actual compile of the intended source. If unchanged source
  reached exact under a disposable experiment, bank it, then remove the experiment.
- **Bounded:** claim a bounded residue only after every applicable lever family has an evidence-backed
  disposition; then mark the complete body with the project's early-stop or stub note. That never excuses
  missing logic, wrong referents, fake code or an unresolved identity.
- **Rule exceptions:** when the bytes need a form that breaks a style rule (not a [match] rule), keep it, and
  write `// RULE-EXCEPTION: <rule>, <reason>` at the code. The form must still pass the reader test. A form that
  breaks a [match] rule is not an exception: the function stays `MATCH-PENDING`, and the source is kept as the
  best-known state.
- **Short batches** may stop sooner; list the remaining hypotheses as open in the handoff.

Commit the focused source, any reusable pattern notes, and the score ledger once `build` is clean and the gate is
green.

Report, per function:
- the score change;
- the rule status: matched, `MATCH-PENDING` (with the rule findings and the fakematch it fits), or
  `ORIGINAL-ASM`;
- the structural correction and its evidence;
- the compiler controls tried;
- the referent verdict;
- the names given and their evidence, and the names still open;
- the `RULE-EXCEPTION`s recorded;
- any remaining wall.
