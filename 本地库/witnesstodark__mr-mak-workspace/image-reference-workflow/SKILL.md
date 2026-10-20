---
name: image-reference-workflow
description: Explore image concepts and make faithful edits of accepted references for 3D or creative production, with explicit model choices and visual review.
---

# Image references and faithful edits

Choose exploration or editing from the user's request. Exploration varies design
dimensions; editing preserves an accepted asset and changes a named feature.
Inspect supplied images before choosing the operation. Respect the requested
provider, model, output count, aspect ratio and intended use.

For fal.ai execution, use the bundled [fal skill](../fal-ai-generation/SKILL.md).
Another provider can be used when requested; inspect its live model schema.

For concepts, vary silhouette, construction, proportions or palette deliberately.
Label candidates with stable names and keep each prompt. For an edit, identify
what remains unchanged and the exact delta. Use the accepted image as input,
not a reconstruction of it from text. A two-image merge must explain the role
of each reference. Avoid injecting extra style adjectives that redesign the asset.

Choose the camera for the deliverable. A hero concept can use dramatic framing;
a modeling sheet needs readable parts and neutral light. Do not force the same
camera on every task. When extraction is requested, use the character-sheet
module rather than treating a cinematic illustration as a complete parts pack.

Keep prompt, endpoint, seed when available, request ID and downloaded outputs
together. Review identity, framing, missing parts, unintended additions and the
requested change. Compare at full size. Keep rejected takes with a short reason,
and preserve the chosen take while making revisions. Present images with direct
file access and a useful preview, using the recipient's existing report style.

Example: "Make two observatory robot concepts with different silhouettes."
After a selection: "Keep B exactly; change only its blue paint to green."
Expected review: the edit retains B's shape, camera, materials and small details.
This is an agent workflow, not an automatic quality classifier.
