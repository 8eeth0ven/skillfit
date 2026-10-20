---
name: game-level-design
description: Turn a game-level brief or existing scene snapshot into a reviewable spatial plan, then apply approved changes with coordinate, navigation and scene checks. Use for layouts, encounter placement and terrain plans.
---

# Game level design

Establish the play goal, scale, camera, movement/navigation limits and existing
visual setup. Inspect the scene and documented mechanics before proposing
placements. Reuse approved lighting/material settings when making another level;
a new layout does not imply permission to redesign the game's presentation.

## Keep source and proposal separate

For an existing level, capture a read-only source snapshot with scene identity,
units, origin, axis convention, terrain/navigation data and object IDs. Record
source hashes or revisions. For a new level, label the baseline as a proposal;
do not describe a generated map as an engine export.

Store edits separately: layer overrides, marker additions/moves/removals and
design notes. Keep alternate layouts independent. Regeneration must not silently
replace a user's edited draft. On a changed source, preserve a recovery copy and
resolve conflicts rather than treating the draft as disposable.

## Make the plan useful for decisions

Show terrain, passage, obstacles, cover and objectives as distinct layers.
Define brush/cell sizes in world units. Visual ground colour is not necessarily
a navigation blocker; tree cover, water and a road may have different rules.
Preserve stable marker IDs and distinguish counts, capacity and starting occupants.
Unchosen prefabs or mechanics remain explicit design intent.

Check main/alternate routes, chokepoint width, clearances, encounter order and
travel distances against actual character sizes and speeds. A 2D simulation can
compare strategies only within its documented assumptions. Its result does not
prove native navigation, combat behaviour or final balance.

## Apply only the approved plan

Export a manifest mapping coordinates, source revision and markers to engine
assets. Reject stale/conflicting revisions before applying. Confirm the target
scene and which objects are generated; do not overwrite an unrelated authored
scene or manual edits as a side effect of a rebuild.

Verify saved terrain dimensions, height/axis conversion, prefab references,
colliders, navigable paths, spawn locations and camera bounds in the engine.
Traverse representative routes and test the changed encounter flow. Preserve
unrelated gameplay values and assets. Deliver the editable plan, applied scene,
export manifest, native captures and unresolved choices.

Example request: "Plan a small valley with two routes to the objective, then
apply the chosen version." Success includes a reviewable layout, measured route
clearance and a verified native path through the saved scene. Dependencies:
project design rules; an editor bridge/CLI or engine access for scene work.
