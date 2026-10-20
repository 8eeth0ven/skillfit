---
name: motion-reference-workflow
description: Prepare and select character motion references, or transfer approved motion to a human reference for a later mocap workflow.
---

# Motion references

Resolve whether the user needs a character reference video for authored animation
or human footage for a later mocap tool. The camera follows that purpose.
Character-first and human-first are both valid; preserve the user's chosen route.

Establish the opening pose, action, contact point, recovery, duration and camera.
Use the approved character identity. Before a new video, verify its first-frame
pose instead of relying on a model to invent the correct start. Keep framing
stable enough to read the relevant limbs and contacts.

Choose the provider/model from the user's selection or current discovery. Use
the [fal](../fal-ai-generation/SKILL.md) or
[Higgsfield](../higgsfield-workflow/SKILL.md) module for execution and recovery.
The number of candidates comes from the task; do not impose a costly fixed batch.

Review support changes, strike readability, foot contact, impossible joints,
interpenetration, unwanted camera motion and loop seams. Keep candidate names
and decisions stable. Preserve longer source motion when creating a shorter
gameplay variant, and record event times in seconds as well as frames.

For an appearance transfer, use the accepted video as motion authority and the
approved human/reference image for appearance. Preserve camera and timing; do
not recreate the action from text. Check the transferred limbs and contacts.
Generated human-looking footage is not itself captured skeleton data. A later
mocap extraction and its quality checks remain separate work.

Keep a small take ledger: source, prompt or edit intent, provider/model, local
result, observed problems and decision. Distinguish generated, reviewed,
selected and approved. Carry the selected take's identity into the animation
handoff. For a creature-to-human transfer, verify which limb represents each
contact and reject anatomy changes that destroy the original action. Preserve
the original and any timed trim; do not replace a motion reference with a new
performance merely because its appearance is cleaner.

Example: a two-second robot walk loop with fixed camera and readable foot
contacts. A successful clip must loop cleanly and retain the approved robot;
remote completion alone does not establish those properties.
