---
name: game-animation-integration
description: Integrate approved character clips into a game's movement and combat systems, including turn compensation, gait phase, event timing and interruptions. Use after animation authoring or to repair runtime transitions.
---

# Game animation integration

Start with the approved rig, runtime export and clip manifest. Inspect the
existing animation player and movement authority before replacing anything.
Confirm forward/up axes, scale, bone paths, import type, bind pose, clips, loop
flags and event times. Keep source animation approval separate from import
verification and in-game visual acceptance.

## Separate movement, facing and authored motion

Choose which system owns translation and yaw. Applying controller rotation and
the same authored turn twice produces a false turn. Keep uncompensated source
clips for pure previews where useful; document the compensated gameplay route.
Record heading samples and their frame/time origin. Derive sample spacing from
the actual count and duration, not a presumed integer or quarter-frame step.

Do not change base movement speed, attack cadence or navigation responsiveness
incidentally. A character need not complete an entire turn clip before obeying
a new movement or combat order. Keep visual stepping speed, gameplay facing and
speed recovery independently configurable.

## Match the pose at a transition

If leaving a partial turn causes a foot swap, longer crossfading alone may not
fix it. Compare the last evaluated pose with sampled gait phases in a shared
body-local space, excluding world placement and controller yaw. Select a nearby
phase at the handoff, then advance normally. Preserve an already better phase.

Build a mapping for the actual anatomy: two feet/knees for a biped can be useful;
four-legged rigs need all relevant paws and support joints. Do not prescribe one
sample count, stride or blend duration for every rig. Bake reusable pose tables
at import/update time; cache bones and avoid allocating or searching each frame.
Rebuild when the rig, clips or coordinate convention changes.

Verify intermediate transforms during a finite transition, including upper-body
settling. A correct mixer weight does not prove a continuous visible pose. Keep
straight and steering variants phase-compatible. Document any root-motion or
contact-IK system separately from phase selection.

## Bind events and validate

Use actual contact/release markers and the game's authoritative clock. Some
custom animation players do not dispatch imported AnimationEvents; verify the
chosen route rather than assuming it. Cancellation must suppress events that
have not happened. Check attack variants, death, pauses and repeated commands.

Exercise left/right, small/large and reversed turns; Walk/Run exits; Stop/arrival;
turn-to-attack; death; disable/re-enable and any storage flow. Review normal speed
from the game camera as well as isolated clip playback. Preserve material/team
bindings, existing prefab GUIDs and unchanged gameplay values.

Deliver the bone/clip mapping, runtime configuration, source contact times,
verified interruption cases and native evidence. Mark missing clips explicitly.
Example: integrate a robot's quarter-turns without changing its movement speed;
prove a partial turn can enter Run without swapping the supporting foot.
Dependencies: approved clips, their editable source/manifest and engine access.
