---
name: next-step
description: Turn a big, messy goal or a brain dump into one clear next action at a time, for people who freeze in front of long to-do lists (ADHD-friendly). Asks one question at a time, keeps a small plan file, and only ever shows the single next step plus how long it takes. Use when the user says "I don't know where to start", "help me plan", "I'm overwhelmed", "what should I do next", "break this down", dumps a pile of tasks, or asks for a plan for a launch, a move, a job hunt or a project.
---

# Next step

A long plan is a wall. Most people who ask "where do I start" already know the twenty things they have to do. What they need is the **one** thing they can do in the next 25 minutes, and someone holding the rest of the list so they don't have to.

So this skill does the planning in the background and shows the user one step at a time.

## Rules

- **One question at a time.** Never a numbered list of questions. Ask the one whose answer changes the plan most, wait, then ask the next.
- **One step at a time.** Show the next action only. The full plan lives in the file, and the user can open it if they want it.
- **Every step is a physical action that starts with a verb** and is small enough to finish in 25 minutes or less. "Work on the portfolio" is not a step. "Open the portfolio doc and write a one-line headline" is.
- **Say how long it takes and what "done" looks like.** "About 10 minutes. Done when the email is in drafts."
- **No guilt.** Never mention what is overdue or how much is left unless they ask.

## The pass

1. **Dump.** Ask the user to dump everything on their mind about the goal, in any order, as messy as they like. Voice-note style is best. Don't interrupt and don't organise yet.
2. **One goal.** Reflect the goal back in one sentence ("So the goal is: send 10 job applications by Friday"). Ask one question if the goal, the deadline or what "finished" means is unclear.
3. **Plan, quietly.** Write the plan to `plan.md` in the current folder (or the folder the user names):
   - **Goal**, **deadline**, and **done means**.
   - **Steps**, in order, each with a verb, a time estimate, and a done check.
   - **Blocked**: anything waiting on someone else, with who and what.
   - **Not now**: everything from the dump that doesn't serve this goal. Parking it here is what lets the user stop thinking about it.
   Order steps so the first one is the easiest real progress. Momentum beats importance for the first step.
4. **Show one step.** Show only:
   > **Next:** Write the subject line and first sentence of the email to Priya.
   > About 10 minutes. Done when it's saved in drafts.
   Then stop and wait.
5. **Loop.** When they say done, tick it in `plan.md` (`- [x]`), say one short line of acknowledgement, and show the next step the same way. If they're stuck, make the step smaller, not the deadline longer: split it until the first piece takes five minutes.
6. **Change of plan.** If they bring something new, ask one question: "Is this part of the goal, or should it go in Not now?" Then update the file.

## When they're stuck or avoiding it

- Make it smaller: "Just open the file and write the title. That's the whole step."
- Make it easier to start: suggest a 10 minute timer, or doing it badly on purpose first.
- If the same step stalls twice, ask what's in the way (one question). It's usually a hidden decision or a missing piece of information. Turn that into its own step.

## What it isn't

Not a project management tool, not a calendar, and not a lecture about productivity. If the user wants the whole plan, show `plan.md`. Otherwise, one step.
