---
name: video-watch
description: Inspect a local or publicly accessible video through sampled scene frames, timestamps and a visual report, especially for motion and 3D reference analysis.
---

# Video Watch

Read [the workflow](../../../knowledge/video-watch.md). Use the project helper
at `scripts/video-watch/extract.py` with a local file or supported video URL and
a new dated Workspace folder. Install its optional dependencies in a local
virtual environment, not the system Python environment.

Inspect the extracted frames. Cite timestamps for observations and open the
original clip when a sparse sample cannot establish timing or continuity.
For gait and fast action, use denser samples around the relevant range. Do not
claim to have watched every frame from a contact sheet.

Keep visual observations separate from audio or transcript claims. URL downloads
in this helper prefer video-only streams; do not assume they contain audio.
For transcription, use the original audio through
a separately configured tool. Create an English summary with evidence and links
in the existing task card. Use `workspace-authoring` for its presentation.
