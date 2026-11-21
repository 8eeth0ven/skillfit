---
name: video-script
description: >-
  Brainstorm short-form video ideas and write scripts that hold viewers, using the creator's
  own video analytics. Use when deciding what to post next, choosing an angle or hook, writing
  or tightening a script before filming (talking-head or narrated explainer), or turning a
  posted video's insights into lessons.
---

# Video script

A short video is mostly decided before filming, by three choices: the **stake** (who, beyond insiders, has a reason to care), the **first two sentences** (why keep watching), and the **proof** (what the viewer sees that makes the claim real). Make each choice from evidence: the creator's own past videos first, platform statements second, taste last.

## Set up

`SKILL_DIR` means this skill's folder. Read `~/.video-script/profile.md` if it exists: it names the creator's video library, findings file, platform notes, voice and pace. Before proposing anything, read the findings file (including tests still running) and the library index, and cite the past videos an idea resembles. Where the findings conflict with a default below, the findings win: they were measured on this audience.

With no profile, ask once for the platform, the audience, and a past video that did well and one that didn't, with their numbers. Then offer to create the profile and a library in the [library format](references/library.md).

**Goal** means what a video is built for: reach (views from non-followers), follows, saves or shares. When the request names none, assume reach and say so.

The tasks are **Ideas**, **Script** and **Review** of a posted video. This skill ends at a script or a lesson: filming is the creator's, editing video-edit's, animation animated-video's.

## Ideas

Start from the latest saved backlog (the profile says where) and fresh material: what the creator built, learned or lived through recently (ask; without an answer, use their latest project folders), news in their field from primary sources with dates, viewer questions if shared, and the library's winners and losers. Mark a premise you couldn't confirm at its source as unverified.

Go wide before judging: candidates that differ in kind, not variations of one idea. They come out wider when a separate agent brainstorms from the material alone, without this skill's rules, and the judging happens afterwards.

Judge them against the goal by the three choices: a stake that lands outside the niche, proof the creator has or can capture, and a hook that surprises about the viewer or what's on screen. A pattern that failed in the library is worth retrying as a deliberate test of a fix. Hold an idea that would muddle a running test until that test is read.

Develop the strongest for the creator to choose between, each with its first two sentences (the first finishing within 3 seconds), the proof the viewer will see, and the finding or open hypothesis it relies on or tests. Two versions of one idea that differ mainly in the opening are one [trial pair](references/insights.md#testing). Save the rest as a one-line backlog.

## Script

State the idea in one sentence, with its goal. An idea that needs two sentences is two videos; ask which to make first.

Find the payoff and the strongest proof before the hook, then write the hook from the most surprising true claim or proof you have. Draft at the creator's pace (from the profile; default 3 spoken words a second). Three moments are tied to the clock; the rest takes the story's own shape:

- **0–3 s, the hook**: about the viewer's stake or what's on screen. Credentials come later, as the reason to believe.
- **3–10 s, the second sentence**: answers the hook or raises its stakes. Most avoidable losses happen here, so background waits. Background is anything the viewer needs only to follow a later detail (history, who someone is, how something works); the test: if moving a line past 15 s loses nothing in the first 15, it's background.
- **The end**: the payoff, the hook's promise shown on screen, then at most one short call to action. Anything after the payoff plays to a leaving audience.

For an **explainer** (how something works), read [explainers](references/explainers.md) before drafting.

Beside every line, write what the viewer sees and the capture it needs (screen recording, document, the real person or product). A line nobody could draw is one the viewer has to hold in their head. For an animated film this column is a note to animated-video, which designs the world.

Deliver, and save where the profile says: the script as time, spoken line and on-screen picture; the capture list; a draft caption carrying the caveats and links the spoken script can't; the estimated runtime; alternative hooks, each with its own second sentence, when the opening is still open; and the claims to verify, with sources (flag any source you couldn't open). Have a fresh agent check each claim as worded in the script against its source: research that is right can still be overstated in the script.

When the creator rewrites some lines, carry the stylistic differences to the lines you still own. Keep their wording unless asked to edit it, and raise factual problems in it separately.

### Checklist

Hold the script against these, the findings file and the platform notes before delivering it:

- One idea. A list earns its place only when every item proves that idea.
- The stake is framed by who it affects, in words a non-expert knows. Tool names and jargon come once the viewer has a reason to care.
- Every claim is shown. Voice, caption and screen give the same number.
- Every promise in the hook is paid off on screen.
- Every sentence, read on its own, says who does what to what, and where any result goes. Replace omitted objects and ambiguous references with the noun; keep pronouns whose referent is clear. Revisions break this, so check again after each one.
- Lines are full, connected sentences in the creator's voice (the voice guide the profile names), easy to say aloud. A line cut so short that it raises a question ("the full route" of what?) costs more than the seconds it saves.
- Each line moves the story forward (a line that restates the one before or announces what's coming doesn't), and the runtime is as short as the story allows.

## Review a posted video

- Record every number: views, viewers, average watch time, follows, interaction counts, each rate with its label, views by source, and the retention curve with its duration ([reading insights](references/insights.md)). From a screenshot, read the curve with `python3 SKILL_DIR/scripts/retention_curve.py SHOT --duration SECONDS` and check its area-based average against the app's figure. Identify each screenshot's video from its thumbnail, graph dates and view count; ask when that evidence can't decide.
- Line the curve up with the final render's captions: for every cliff and plateau, record what was said and shown in the seconds before it. Compare with the library: videos in the same format, and every video's 3→10 s drop.
- Write the video's library entry and index row, then update the findings file: add the evidence to each hypothesis it touches, and change a status only when two or more videos agree. Before saving, take every quoted line and time from the captions file, not a summary; give a posting date only with its source; check every ranking word (highest, lowest, only, best) against the index, scoped to the videos it covers.
