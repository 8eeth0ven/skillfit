---
name: decomp-code-rules
description: Coding rules for matching-decompilation source - declarations, names, literals, structure, layout and honesty of reconstructed C/C++ - with tiers that say which rules can change compiled bytes and which ones a function must pass before it counts as matched, a catalogue of fakematches versus genuine idioms, and naming/layout defaults taken from id Software's engines. Use when writing, reviewing, cleaning up or linting decompiled source, when judging whether a byte-identical function is a real match or a fakematch, when choosing a naming or layout style for a decomp project, when adding or relaxing a project rule, or when building a rule checker.
---

# decomp-code-rules: source that matches *and* reads like the original

**Files:**
- [references/rules.md](references/rules.md) is the full catalogue, with examples. Read the sections you need.
- [references/style-defaults.md](references/style-defaults.md) has the naming and layout tables to start from
  when the original's own style is unknown.
- The project's `AGENTS.md` holds the **project profile**: compiler dialect, naming style, placeholder patterns,
  evidence sources, commands, and any rule the project tightens or relaxes. The project profile overrides this
  skill.

## Why: the reader test

A decompilation exists so people can understand the original program. Matching bytes prove the source is
faithful; readable source is the point. Every rule serves one test:

> Would a programmer on the original team, writing in that codebase's style and dialect, have typed this?
> And can a reader see what it does, and why, without opening the disassembly?

A **fakematch** fails this test while producing the right bytes: a dummy temporary, a `volatile` carrier, an
empty block, a reused variable, an offset cast. It is a clue to the real source, not a match.

The era's real idioms pass the test, however dense they look today: `*dst++ = *src++`, `goto fail` cleanup,
a long function, a bug the original shipped. Section F of the catalogue lists both sides.

## The two laws

1. **The bytes win.** A change made for style must not change what the compiler emits. When a rule and the bytes
   disagree, keep the bytes and write `// RULE-EXCEPTION: <rule>, <reason the bytes give>` at the code. An
   exception bends a style rule. It never licenses fake code.
2. **Identical bytes alone are not a match.** A function counts as matched only when its bytes match *and* it
   passes every **[match]** rule:
   - R1, R2: one declaration per type and global;
   - R4: no offset casts;
   - R13: real vtables;
   - R17: no fake code;
   - R18: no assembly bodies.

   Byte-identical but failing is `MATCH-PENDING`. Report it, and don't count it. Naming (R7) is not required:
   placeholder names are reported as open work, not as a failed match.

   A [match] rule blocks a match exactly where its checker row fires. Its checks are deliberately narrow, so
   genuine original code (hardware `volatile`, C struct inheritance, placeholder-named real vtable slots) passes.
   A function the original wrote in assembly is `ORIGINAL-ASM`: listed apart, and counted neither way (R18).

## Tiers: what a rule may cost

| tag | before applying |
|---|---|
| [free] | nothing: it can't change the output. Two traps: `__LINE__`, and binaries that record line information (R23). Names are free only where they don't reach RTTI, stringizing macros or debug data (R7). |
| [checked] | run the per-function check and the byte gate after the change |
| [evidence] | have evidence for the name or signature (surviving source, mangled names, RTTI, exports, strings) |
| [match] | required before the function counts; also [checked] when you fix it |

## The catalogue at a glance

| section | rules | covers |
|---|---|---|
| A. Declarations and types | R1-R6, R25-R27 | one declaration per type and global, header shape, typed members, enums, prototypes, typed pointers, readable struct layout |
| B. Names | R7, R8, R28-R30 | evidence-based names, per-module style, module prefixes, naming by kind, one meaning per local |
| C. Literals and operations | R9-R11, R31 | number bases, named bit operations, named constants as expressions, macro hygiene |
| D. Structure | R12-R16, R32-R35 | where functions live, vtables, `goto`, unit order, helpers, unit layout, function headers, no splitting, readable statements |
| E. Honesty of the source | R17-R24, R36, R37 | no fake code, no assembly, casts, `const`, comments, dialect, formatting, quirks labelled, real `#if`s only |
| F. Fakematches and human idioms | table | each fakematch, what it usually hides, and the human form |

## Writing new source

Apply every rule while reconstructing, not afterwards. Offset casts, local type copies, scattered `extern`s and
steering code are scaffolding that must be gone before you report a match. When a spelling matches only through a
trick from Section F, keep looking for what the original programmer wrote. The trick tells you where to look:
- a missing helper or macro (R16, R31);
- a wrong type (R6);
- two variables merged into one (R30).

Placeholder names may remain: report them as open naming work. Never write a confident-sounding invented name.
Use the binary's own evidence first: error strings that start with a function name, console-variable strings,
assert text.

## Reviewing or cleaning up existing source

1. Run the project's rule checker if there is one. Otherwise grep for the [match] patterns in the table at the end
   of the catalogue.
2. **Fix in tiers:**
   - [free] fixes first, in their own commit: banners, braces, comments, layout. Mind `__LINE__` and line
     information (R23), and run the byte gate once per batch anyway.
   - Then each [checked] or [evidence] fix, with its checks.
   - Never mix formatting with code changes.
3. A fix that breaks a match is reverted or reshaped, never kept. A rule the bytes defeat gets a
   `RULE-EXCEPTION`.
4. Read each matched function once more against the reader test. Section F names what to look for.
5. Report:
   - the [match] violations fixed, and the functions they moved from `MATCH-PENDING` to matched;
   - the fakematches found;
   - the exceptions recorded;
   - what is still open.

## Changing the rules

A project may tighten a rule (for example, make R15 or R33 [match]) or relax one (for example, allow `goto`
freely), in its `AGENTS.md` with the reason. Move a rule into [match] only if it can be checked mechanically, and
update the checker in the same change. A rule nobody can check turns "matched" into an argument. Rule numbers are
stable identifiers: add new rules with the next free number, and never renumber.

## Linting tools and outside style guides

A generic code-quality linter or a modern style guide can find candidates, but it doesn't know the bytes win:
- its fixes can change codegen or mangling: renames, reordering, extracted helpers, `const`, enums, a two-return
  limit, `default` in every switch, null checks, `do { } while ( 0 )` wrappers;
- many of its findings are required by the binary: "dead" functions, duplicate inline copies, original
  complexity, original naming style, the original's own bugs (R36).

Use such tools read-only. Route every fix through the checks, and record legitimate findings as exceptions rather
than chasing a score.
