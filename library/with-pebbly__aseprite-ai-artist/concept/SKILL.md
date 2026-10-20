---
name: concept
title: Design it first — concept sheet and storyboard
description: Before drawing a new character, prop, scene or animation, write an art spec, turn it into a ready-to-paste prompt for an image-generation model, and offer the user a choice — generate a concept sheet or storyboard with it and send it back, or continue without one. When reference art arrives (from that prompt or from the user), read it into a PixelSpec and import it panel by panel, so the pixel work reproduces a decided design instead of improvising one. Use after the brief for anything drawn from scratch, and whenever the user supplies reference art; skip for edits to existing art.
---

# Design it first — concept sheet and storyboard

Drawing from nothing asks one model to invent a character, a pose, a camera, a
palette and the placement of every pixel, all at once. It is the step where
generated pixel art falls apart. Split the job:

- **An image model owns the design** — the look of the character, the key
  poses, the storyboard. That is what those models are good at.
- **You own the pixel interpretation** — reading that design into a canvas,
  a palette and a set of shapes, then drawing it with the rules.

The reference is a guide for proportion, pose and colour masses. It is never
the pixels: a concept downscaled onto the canvas is anti-aliased mush, and no
amount of cleanup turns it into pixel art (see *What this must not do*).

## Two modes

| The user gave you | Mode | Start at |
|-------------------|------|----------|
| Only words ("a fire mage with a walk cycle") | **Creative** — spec → prompt → offer | step 1 |
| An image — concept art, a sketch, a screenshot, a sheet | **Reference** — read it, import it | step 5 |
| An edit to art that already exists | neither — use `aseprite:fix` | — |

## Procedure

### 1. Start from the brief

`aseprite:brief` has already fixed canvas size, palette, view, light, outline
and destination. Do not ask any of it again. The prompt needs colours, not a
palette's name: for a preset, read its hex values from the
`knowledge://palettes` resource (no document has to exist yet); for an open
sprite, `palette op="get"`.

### 2. Write the art spec

Short, concrete, in working notes. Everything the image model and, later, you
will be held to:

- **Subject and scenario** — who or what, one line of personality, and for an
  animation what happens from the first frame to the last.
- **Target** — canvas W×H, how many pixels tall the subject stands, view and
  facing, light direction, outline style.
- **Silhouette** — heads tall, the two or three shapes that must read at 1×
  (a pointed hat, a long coat, an oversized sword).
- **Palette** — the exact hex list with roles: outline, skin ramp, cloth ramp,
  metal ramp, accent. Its size is the ceiling.
- **Animation** — cycle, frame count, one line per key pose, timing in ms, loop
  or one-shot. Plan it with `rules://05-animation` (or the `animation-director`
  agent) — the storyboard panels are these keys.
- **Must not** — text, background scenery, props that are not in the brief,
  camera changes between panels.

### 3. Build the prompt

In English whatever language the conversation is in — image models follow
English prompts best. It has to produce something you can slice with
`reference op="import" grid=…`, so the layout contract is not optional:
equal panels, one row, same scale and ground line in every panel, flat
background, no text.

For a character or prop — a **concept sheet**:

```
Pixel art character concept sheet of {subject}: {one-line personality}.
{view} view, {facing}, light from the {light}. Low-resolution pixel art look:
the character is about {height}px tall on a {W}×{H} sprite, hard pixel edges,
no anti-aliasing, no gradients, {outline style} outline.
Palette — use only these colours: {hex list with roles}.
Layout: {n} panels in a single horizontal row, equal width, evenly spaced,
the same character at the same scale in every panel, feet on the same ground
line: {panel 1: front | panel 2: side | panel 3: back | …}.
Flat plain {#ffffff or #808080} background, no scenery, no text, no labels,
no borders, no watermark.
```

For an animation — a **storyboard**, one panel per frame:

```
Pixel art animation storyboard of {subject} performing a {cycle}.
{view} view, facing {facing}, camera locked, light from the {light}.
Low-resolution pixel art look: the character is about {height}px tall on a
{W}×{H} sprite, hard pixel edges, no anti-aliasing, {outline style} outline.
Palette — use only these colours: {hex list with roles}.
Layout: exactly {N} panels in a single horizontal row, equal width, evenly
spaced, identical character size and ground line in every panel — each panel
is one frame, left to right:
1. {key pose 1}
2. {key pose 2}
…
{N}. {key pose N}
Flat plain {background} background, no motion lines, no text, no numbers,
no borders, no watermark.
```

Ask for both when the request is an animated character: the sheet fixes the
design, the storyboard fixes the motion. Fill every `{…}` — a prompt with a
placeholder left in it produces a generic character.

### 4. Offer the choice — once, in one message

Put the prompt in a single fenced code block, so it copies in one action. If
the brief is still awaiting confirmation, this is the same message — decisions,
prompt, choice — not a second round trip. Then offer exactly these options,
through the harness's question tool when it has one (Claude Code's
AskUserQuestion, omp's `ask`), otherwise as a numbered list:

1. **"I'll generate references"** — the user pastes the prompt into any image
   model (ChatGPT, Gemini, Midjourney, …) and sends the result back. Ask for
   the image **as a file path** — saved to disk, or dragged into the chat where
   the harness turns that into a path — because `reference import` reads
   files, not pixels you have only seen in the conversation.
2. **"Continue without references"** — go straight to drawing from the spec.
   The spec still binds: it is the design now.

If your harness has an image-generation tool, add it as a third option ("you
generate it"), never as a silent default. When the user chooses option 1, stop
and wait for the image; do not start drawing in the meantime.

### 5. Read the reference into a PixelSpec

Look at the image first, then write down what you read — before any pixel is
placed. This is where the design becomes decisions you can check against:

```json
{
  "canvas": [32, 32],
  "view": "front-3/4",
  "source": { "path": "…/storyboard.png", "panels": 4, "panelSize": [256, 256] },
  "silhouette": { "head": [11, 3, 20, 11], "torso": [10, 12, 22, 22], "staff": [23, 2, 25, 30] },
  "landmarks": { "eyesY": 8, "waistY": 18, "feetY": 30 },
  "palette": { "outline": "#1d2b53", "robe": ["#7e2553", "#ff004d"], "skin": ["#ab5236", "#ffccaa"] },
  "frames": ["contact, staff forward", "down, 1px lower", "pass, 1px higher", "up"],
  "deviations": ["belt buckle and runes dropped — 1px at this size is noise"]
}
```

- **Coordinates are target pixels**, not source pixels: scale what you see down
  to the canvas and write the result. Bounding boxes are `[x0, y0, x1, y1]`.
- **Palette**: sample the panel — `reference op="sample_palette" path=… region=…`
  — then map each colour mass onto the sprite palette. Do not adopt the
  sampled colours; an image model's "four colours" are forty.
- **Deviations** are the design decisions the pixel version makes on purpose:
  what does not survive at this size and is simplified or dropped. Listing
  them here is what lets the review loop tell a deliberate change from a miss.
- No reference (the user chose to continue)? Write the same PixelSpec from the
  art spec alone. It is still the thing the drawing is checked against.

### 6. Import it

After `aseprite:new` has made the document:

- **A concept sheet** — import the panel for the view you are drawing:
  `reference op="import" path=… region={x, y, width, height}` (source pixels).
- **A storyboard** — create the frames first (`frame op="add" count=N-1`),
  then one call puts panel i on frame i of a single reference layer:
  `reference op="import" path=… grid={columns: N, rows: 1}`. Panels that are not
  evenly spaced: one `region` import per panel, each with its `frame`.
- `look op="compare"` on frame 1: the left half is what you imported. Wrong
  panel, or the character cut off? Fix the region now, not after drawing.

### 7. Hand over to drawing

`aseprite:draw` (or `aseprite:animate` for a storyboard) does the work, over
the reference. The loop that makes a reference pay off:

1. `look op="compare"` — reference left, art right, same scale.
2. Name the **three to five largest mismatches** — silhouette, proportion,
   pose, placement of colour masses. Not "improve it": a list.
3. Fix only those, in one `draw` call.
4. Compare again. Stop when every remaining mismatch is a listed deviation.

Two rounds is normal. Remove the reference layer before export
(`reference op="remove"`) — `aseprite:export` checks for it.

## What this must not do

- **Pixelize the concept.** Importing the reference and calling it the art,
  copying its pixels through `read_pixels` into `draw`, or recolouring it into
  the palette all produce the same AI mush. Draw the sprite; use the reference.
- **Ask twice.** The spec, the prompt and the choice are one message.
- **Hide the prompt in prose**, translate it, or leave `{placeholders}` in it.
- **Draw while waiting** for a reference the user said they would send.
- **Treat the reference as more authoritative than the brief.** If the image
  model changed the palette, the view or added a cape nobody asked for, the
  brief wins — note it as a deviation.

## Related

`aseprite:brief` before this, `aseprite:draw` and `aseprite:animate` after it.
`rules://03-silhouette-and-form` for reading proportions,
`rules://01-palette-and-color` for mapping colours onto a palette,
`rules://05-animation` for key poses.
`rules://36-character-design` for shape language and silhouette,
`rules://37-views-and-directions` for the camera, `rules://91-composition-and-scenes`
for anything with a background, and the subject rows of `skill://studio`.
