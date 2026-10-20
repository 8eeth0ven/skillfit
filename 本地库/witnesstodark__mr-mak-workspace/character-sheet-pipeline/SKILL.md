---
name: character-sheet-pipeline
description: Prepare strict-front character sheets, isolated parts and optional multiview references for 3D modeling from an approved image.
---

# Character sheets and isolated parts

Create a consistent reference pack from the user's supplied character. This is
an agent-guided workflow with prompts and visual inspection; it does not bundle
a standalone classifier or an automatic mesh-generation service.

Use the supplied design as authority. Establish the relevant parts, symmetry,
pose and downstream use. Preserve already approved scope; do not ask again for
an approval the user has given. Optional views and videos are separate scope.

1. Inspect the reference and propose the useful body/accessory inventory.
2. Prepare a strict-front A-pose sheet using [01a](prompts/01a_apose_front.md).
   Match the character's anatomy; keep feet and hands visible, lighting flat and
   the background neutral. Check identity and pose before extracting parts.
3. A supplementary multiview sheet can help communicate the whole design:
   [01b](prompts/01b_character_sheet.md). It does not replace the approved front
   source for extraction.
4. Extract approved parts from the same source: [body](prompts/02_parts_body.md),
   [paired items](prompts/03_parts_paired.md), [accessories](prompts/04_parts_accessory.md)
   and [hair](prompts/05_parts_hair.md). Keep the front camera and original pose.
   Do not turn isolated props into hero shots or add new equipment.
5. Inspect every image with the host's image tools or an explicitly configured
   vision service. [08](prompts/08_3q_classifier.md) supplies the front-view
   rubric. Record pass, soft failure or hard failure with reasons. Retry a failed
   criterion within the task budget; repeated failure is a decision to surface,
   not a reason for an unlimited paid loop.
6. If requested, add [side/back views](prompts/06_multiview.md) for selected parts.
   If requested and budgeted, add [turntables](prompts/07_360_video.md), with a
   locked camera and rotating subject. Do not create optional video by default.
7. Deliver an inventory with prompt, provider/model, source hash, local files
   and review verdicts. Label which source is approved and which outputs still
   need a decision. Keep texture, rigging and mesh generation as later tasks.

Nano Banana Pro front/part edits and GPT Image supplementary sheets are useful
routes from the source workflow, not restrictions on a user's explicit choice.
Verify current endpoint IDs and schemas via the selected provider. The included
[fal module](../fal-ai-generation/SKILL.md) handles fal execution and job recovery.

Example: a robot with three feet and one telescope. Extract the body, telescope
and foot set from the approved front reference. Acceptance means matching shape,
pose and lighting, with no missing foot and no new perspective drift.
