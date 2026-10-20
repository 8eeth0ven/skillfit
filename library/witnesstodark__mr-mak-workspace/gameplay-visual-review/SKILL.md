---
name: gameplay-visual-review
description: Verify a visual game change using controlled native captures, targeted behavioral checks and a reviewable evidence record. Use for animation, VFX, HUD or scene changes whose appearance must be judged in the actual game.
---

# Gameplay visual review

Read the requested change and its accepted baseline. Choose a short test that
can reveal the difference. Preserve the current scene and unrelated systems;
inspect editor state before taking control, and coordinate if another agent is
already using the same editor. Do not restart an active tool merely for a capture.

## Build a fair comparison

Use the game's actual camera, lighting, materials and normal playback speed.
Keep seed, subjects, route/action and framing comparable for OFF/ON or before/after
captures. Record any unavoidable difference. A slow-motion close-up is useful
diagnostic evidence, but it should not replace normal gameplay zoom.

A review lab should isolate the changed feature while retaining its production
code path. Do not "fix" a comparison with a separate demonstration implementation.
If synthetic input is needed, separate it from physical devices and restore
the prior input settings afterward. Discard transient test orders rather than
saving them into the authored scene.

## Check appearance and behavior separately

For animation, inspect contact, seams, interrupted transitions and responsive
controls. For VFX, inspect contrast, overlap, attachment and cleanup. For UI,
inspect readability, overflow, input blocking and real state. For terrain,
inspect scale, grounding, traversal and the gameplay camera.

Counters, hashes and saved values can prove wiring or unchanged inputs. They do
not prove visual quality. A screenshot does not prove a timed transition, and a
passing browser study does not prove native rendering cost. Measure the relevant
system only, and keep unrelated sound/narration quiet during visual-only checks.

## Leave useful evidence

Record the source revision, saved configuration, exact scenario, capture type,
observations and remaining issues. Label generated art, browser schematics,
isolated engine previews and native gameplay clearly. A successful agent check
does not imply the user accepted the result.

Provide short local loops or videos for motion and stills for detail. Keep the
original capture and a lightweight review copy with provenance. Do not repeatedly
recompress an already compressed delivery. Update the current specification when
behavior changes; put chronological details in the development log.

Example: compare a shield impact OFF/ON on dark and pale ground with identical
gameplay. Deliver the visible comparison plus cancellation and cleanup results;
leave final aesthetic acceptance explicit. Dependencies: native engine access
and a local capture method; a report viewer is optional.
