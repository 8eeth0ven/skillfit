---
name: helper-recovery
description: Recover the inline helpers, accessors and macros hidden inside decompiled functions. Read one function at a time, mark where its statements drop below the abstraction level of the code around them (raw member arrays, container internals, repeated expressions, scoped blocks), restore the helper the original developers called, and apply it at every site. Use for helper-recovery passes over sampled functions, for hard walls that may be an open-coded helper, and whenever a function mixes domain operations with another class's internals.
---

# helper-recovery: restore the helpers behind a function

Project guide: the repository's `AGENTS.md`. If the repository has none, use [AGENTS-template.md](../matcher/references/AGENTS-template.md) and ask the user to fill in its project adapter.

The original developers wrote accessors, small inline helpers and macros, and the compiler expanded them. A
reconstruction that transcribes the expanded body reads fine, but it can miss the helper's own statement
boundaries, local scopes, temporaries and evaluation order, and that is often exactly what a stubborn wall is.
Restoring the helper is correct source whether or not a score moves, and once enough helpers are restored, hard
functions start to close.

```diff
-    if (target != 0 && target->m_skillLevel[m_skill] <= m_level) {
-        if (target->m_skillLevel[m_skill] == 0)
+    if (target != 0
+        && target->GetSkillLevel(SkillId(m_skill)) <= m_level) {
+        if (target->GetSkillLevel(SkillId(m_skill)) == 0)
             target->GiveSkill(m_skill, m_level);
```

The caller works with skills; it should not index another class's array. The helper is called twice, not cached,
and that is the original shape.

`AGENTS.md` governs: source rules, scores, the inner loop. This skill is the method.

## 1. Pick a function

Sample rather than hand-pick: a random function reveals habits that a worklist misses. Draw one at random from the
project's function list or score ledger, at any score. An exact function with an open-coded helper is still wrong
source, and its sites teach you the helper for the hard ones. Read the whole function, its class header, and its
callers and callees.

## 2. Read the abstraction levels

Annotate each statement with the level it works at, and look for statements below the level of their neighbours:

- **Another class's internals.** Indexing a member array, walking a list's nodes, or testing flag bits or enum
  ranges of an object the function does not own. The owner almost certainly had an accessor or predicate
  (`GetAt`, `IsAlive`, `HasFlag`).
- **Repeated expressions.** The same field path or computation written twice instead of being held in a local.
  An original call per use looks exactly like this, where a transcriber would have cached it.
- **Scoped blocks.** A `{ ... }` block with its own locals in the middle of a function is the footprint of an
  inlined helper body or macro. Its locals' lifetimes, EH states and stack homes come from that boundary.
- **Casts and conversions at a call site.** `SkillId(m_skill)`-style conversions reveal the helper's typed
  parameter.
- **Idioms.** Clamp/min/max, range checks, bit packing, coordinate maths, lookup-with-default. These were helpers
  or macros far more often than not.

## 3. Find the helper's evidence

A helper needs evidence, not taste:

- **Repetition.** Search for the raw pattern across `src/` and `include/` (`rg`) and count the sites. The same
  expression at several sites, especially in different classes, is the strongest signal.
- **Existing helpers.** Check the owning class and its headers first: the helper may already exist unused, or
  exist for a sibling field.
- **Surviving source.** Check the engine lineage, SDKs and sibling projects for the class or family. When the
  original name and signature survive, use them.
- **Retail shape.** A repeated load instead of a reused register, a reload after a call, or stack homes shaped
  like a scope all corroborate a call per use.

Name the helper for what it means in the owner's domain. Put it in the owning class's shared header (an inline
member, or a macro where the family uses macros), with the typed signature the call sites imply.

## 4. Apply everywhere and measure

1. Replace every site of the pattern, not just the sampled function.
2. Run `build` (the change spans units) and read the score changes.
3. An exact function must stay exact after the rewrite. If it drops, the helper's shape is wrong somewhere:
   by value versus by reference, const, parameter type, statement split, or member versus free function.
   Fix the shape rather than abandoning the helper, or leave that site unconverted and note why.
4. Sub-100 functions may dip on the first shape. Compose further levers on the helper base before concluding.
5. Commit each helper as one focused commit: the helper and all its sites.

A helper that keeps every exact function exact is kept even if no score rises: it is the original source layer.
Do not invent helpers without repetition or retail evidence, and never add one only to move a score.

## 5. Report

For each sampled function, report:
- what it mixed;
- which helpers were recovered (name, owner, site count);
- score changes (new exacts, drops fixed or left);
- any helper you suspected but could not justify.
