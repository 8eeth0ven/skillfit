---
name: materials-to-game
description: Create or apply material maps and bake a textured high-poly mesh onto a game mesh, with channel, UV and export checks.
---

# Materials and game bake-down

Identify the requested operation: generate material maps, retexture an existing
mesh, or optimize a textured high-poly for a game. These are different tasks.
Keep supplied geometry when only a material change was requested.

For fal material generation, discover the current Patina/material endpoint and
read its schema using the [fal module](../fal-ai-generation/SKILL.md). The chosen
material should be evaluated on the intended surface, not only as a preview tile.
For mesh retexturing, inspect the chosen service's geometry/UV inputs separately.

For a high-to-low workflow:

1. Preserve the textured high-poly source. Choose the target budget from the
   asset's role, silhouette, camera distance and engine constraints.
2. Decimate or retopologize into a separate low-poly. Inspect thin parts, hard
   edges and the silhouette. A fixed face count is not suitable for every asset.
3. Unwrap the low-poly, check texel density, seams, overlap and padding.
4. Bake the required detail from source to target. Verify cage/ray distance,
   transforms and selected-to-active direction before trusting the bake.
5. Identify base color, normal, roughness, metalness and any packed channels.
   Color maps and data maps need appropriate color-space settings. Check normal
   orientation in the target renderer; keep packed-channel conventions explicit.
6. Export the low-poly with its maps. Reimport from another directory and check
   material links, scale, silhouette and texture resolution.

Example: a textured brass prop reduced for a distant game camera. Acceptance
requires the same readable silhouette and a clean material at the gameplay
distance; a smaller file alone is not sufficient. Preserve the source mesh.
Dependencies: Blender or the chosen bake tool, supplied geometry/materials,
and a provider account only for a requested remote generation.
