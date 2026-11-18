---
name: skill-router
description: Decide which installed skill, or which chain of two or three skills, fits a task before starting it, and run them in the right order with each one's output feeding the next. Works with any set of skills, because it reads every installed skill's description at run time. Use when a task is big or vague, could fit several skills, or needs more than one ("which skill should I use", "what's the best way to do this", "plan the steps", "use whatever skills make sense"), or when it's unclear whether any skill applies.
---

# Skill router

Pick the right tool before working. One skill done well beats three loosely chained, so prefer one skill, use two when the task truly has two stages, and use three only for a full pipeline.

## 1. See what's installed

```
python3 ~/simcraft/skills/planning/skill-router/scripts/catalog.py            # every skill, with its description
python3 ~/simcraft/skills/planning/skill-router/scripts/catalog.py --grep video
```

Always run it rather than relying on memory. Skills get added and removed, and the description is the contract.

## 2. Pin down the task

Write one line each for:
- **Goal:** what the user wants to be true at the end.
- **Input:** what exists now (a file, a URL, a repo, a vague idea).
- **Deliverable:** the exact artifact (a video, a report, a fixed bug, a doc).

If any of these is unclear and the answer would change the skill choice, ask one question. Otherwise decide.

## 3. Match

For each candidate skill, check three things against its description:
1. **Trigger fit.** Does the task match what it says it's for, not just share a keyword?
2. **Input fit.** Does it accept what the user has?
3. **Output fit.** Does it produce the deliverable, or something the next skill needs?

Keep only skills that pass all three for their part of the work. When two skills overlap, choose the more specific one (a skill made for the exact format beats a general one). If nothing fits, say so and do the task directly. A forced match is worse than none.

## 4. Decide: one, two or three

- **One skill** when it goes from the input to the deliverable on its own.
- **A chain** when the work has distinct stages and each stage has its own best skill. Typical shapes:
  - **understand → make:** analyse something first, then build from what was learned.
  - **make → check:** build, then audit or review it with a separate skill.
  - **raw → clean → finish:** e.g. trim footage, clean the audio, then add graphics.
- Write the chain as a handoff: what each skill produces, and which file or fact the next one takes as input. If a step has no clear handoff, the chain is wrong.
- Never run two skills that do the same job, and never add a skill just because it is related.

## 5. Show the plan, then run

Show the user a short plan before starting anything heavy:

```
Task: <one line>
Plan: <skill A> (<what it gives>) → <skill B> (<what it does with it>)
Why not <closest alternative>: <one line>
```

Then load each skill with the Skill tool in order, follow its instructions fully, and check each handoff before moving on. If a stage's output is weak, fix it there rather than letting the next skill build on it.

## Examples of good chains

These use skills from this repo. The method is the same for any skill set.

| Task | Plan |
|---|---|
| "Remake this viral clip in my style" | reverse-engineer-video (shot list, camera moves, beat map) → perspective-illusion or code-loop (build it) |
| "Turn this paper into a video" | paper-to-runnable (working code + internals animation) → vox-explainer (explainer over a voiceover) |
| "Audit this SDK and show it" | dx-audit (friction log, teardown) → scripted-screencast (recorded journey) |
| "Clean up my talking-head take" | rough-cut → clean-audio |
| "Is this new endpoint safe and well designed?" | api-design-review → security-threat-model |
| "It got slower last week" | benchmark-honestly (a trustworthy oracle) → bisect-anything (find the commit) |
| "I just joined this repo, fix the flaky CI" | codebase-map → flaky-test-killer |
| "Make a branded explainer for a sponsor" | brand-kit → vox-explainer |

## Mistakes to avoid

- Picking by keyword ("video" in the request) instead of by deliverable.
- Chaining when one skill already covers both stages.
- Skipping a stage's own checks to get to the next skill faster.
- Forgetting a skill's safety rules when it runs inside a chain. Each skill's rules still apply in full.
