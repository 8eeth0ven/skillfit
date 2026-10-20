---
name: animate
title: Animate a cycle
description: Build an idle, walk, run or attack cycle from key poses, set timing that reads as motion rather than a metronome, tag it, and review it as a filmstrip. Use when a rigged sprite needs to move.
---

# Animate a cycle

## Before you start

The sprite must be rigged onto named layers — see `aseprite:rig`. Animating a
flattened sprite means redrawing every frame by hand.

## Procedure

### 0. With a storyboard

If `aseprite:concept` delivered a storyboard, its panels are the key poses —
the plan in step 1 is written from them, not invented. Import it once the
frames exist: `frame op="add" count=N-1`, then
`reference op="import" path=… grid={columns: N, rows: 1}` puts panel i on
frame i. Every frame then has its own reference, and `look op="compare"
frame=i` checks that frame against its panel — do that for each key in
step 4. The PixelSpec's per-frame notes and deviations still decide what
survives at this size: a storyboard can suggest a 4px jump the timing
cannot carry.

### 1. Plan the key poses

Write them out before touching a frame. For a walk:

1. **Contact** — front foot lands, back foot pushing. Widest stance.
2. **Down** — weight on the front leg, body **lowest**.
3. **Pass** — legs together, body **highest**. The frame everyone forgets, and
   its absence is why a walk looks like sliding.
4. **Up** — pushing off, rising.

Then mirror for the other leg: 8 frames. A 4-frame walk uses contact and pass
per leg.

Idle: 2–4 frames, a breath — chest rises a pixel, shoulders follow one frame
later. Attack: anticipation, strike, hold, recover.

### 2. Create the frames

```
frame op="add" count=7
```

Already done if a storyboard was imported in step 0 — the import needs them.

### 3. Block the key poses

Move limbs by moving cels, not by redrawing:

```
cel op="copy" layer="arm-near" frame=1 toFrame=3
cel op="move" layer="arm-near" frame=3 dx=2 dy=-1
```

Redraw only where a part genuinely changes shape — a foreshortened arm, a
bending knee. Do that redraw as a grid: `look op="ascii" layer=… frame=…
rulers=false region=…` on the part in the previous key, edit the rows into the
new shape, and `draw` kind `grid` them onto the new frame at the same origin.
Copying the rows first keeps the part's volume from drifting, because every
pixel you did not change stays exactly where it was.

### 4. Look at the keys before adding in-betweens

```
look op="filmstrip"
```

A vision model reads only the first frame of a GIF, so the filmstrip is the
only way to actually see the motion. Check volume and height consistency here,
while there are four frames to fix rather than eight. With a storyboard,
`look op="compare" frame=…` on each key as well: the pose should match its
panel before any in-between is drawn from it.

### 5. Add in-betweens

Only once the keys read. Spacing is your easing: poses close together read slow,
far apart read fast.

```
look op="onion" frame=3
```

Use onion skinning to judge an in-between against its neighbours without
stepping through frames one at a time — it composites the target at full
opacity over ghosted neighbours, oldest-first.

For secondary motion — a bob, a breath, a float — `cel op="tween"` or
`cel op="oscillate"` fill in the in-between cels for you instead of keying each
one by hand:

```
cel op="oscillate" layer="hair-back" fromFrame=1 toFrame=8 amplitudeY=1 period=8
```

**Caveat:** easing rounds each frame's offset to the nearest pixel, and on
small amplitudes (1–2px) that rounding can make two adjacent frames land on
the same value and then jump — a stutter, not a stumble. Prefer hand keys for
primary motion (the walk, the strike); reach for `tween`/`oscillate` for
motion nobody is meant to consciously notice.

**Something that grows or shrinks on screen** — a wagon coming down a road,
a bird flying away — is drawn at three or four sizes by hand (far, middle,
near), each a complete little sprite with all its parts, and every frame uses
the nearest one. Do not compute it from a formula and re-rasterise it at each
size: below about 12 px a scaled shape loses or merges its parts (the wheels
vanish, the cover becomes a blob), and it changes shape from frame to frame.
Before you finish, `look op="preview" frame=<n>` on the frames where it is
largest and smallest.

### 6. Set timing

```
frame op="set_duration" durations=[150,100,100,150,150,100,100,150]
```

Hold contact poses longer than pass poses. Uniform timing reads mechanical no
matter how good the drawings are. Typical ranges are in `rules://05-animation`.

### 7. Tag it

```
tag op="create" name="walk" from=1 to=8 direction="forward"
```

Untagged frames are unusable by a game engine. `validate` treats a multi-frame
untagged sprite as an error.

### 8. Review

`look op="filmstrip"` again, then run through the animation checks in
`rules://07-review-checklist`: consistent volume, consistent height, clean loop,
anticipation before strong actions, light that does not move. Run `validate`
with an `expect` describing the cycle — which layers live on which frames, which
parts must never overlap — so the mechanical check knows what "right" means here.

## Related

`rules://05-animation`, `rules://06-layers-and-rigging`, `rules://40-timing-and-spacing`.
For the cycle itself: `rules://41-idle-and-breathing`, `rules://42-walk-and-run`,
`rules://43-jump-fall-land`, `rules://44-attacks-and-impacts`,
`rules://45-secondary-motion`, `rules://46-subpixel-animation`,
`rules://47-top-down-animation`; animals: `rules://51-animal-gaits`,
`rules://52-birds-and-flight`. Their frame tables and key-pose templates come
before your own invention.
