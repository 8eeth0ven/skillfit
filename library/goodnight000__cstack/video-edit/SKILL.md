---
name: video-edit
description: >-
  Edit and revise talking-head videos, social reels, text-overlay skits and memes,
  reel recreations, demos, and screen recordings, including animation, logos and
  motion graphics added over existing footage.
  Use for quiet-audio recovery, separate-audio sync, preprocessing, take selection, DaVinci Resolve editing,
  relevant sourced visuals, captions, speed or color corrections, and authorized
  video publishing or scheduling. Also use for post-edit reflection and updates
  to this editing workflow.
---

# Video edit

Make the video's idea land for its style. A valid render is only one part of a
finished edit.

## Set up

On a new machine, run `python3 SKILL_DIR/scripts/preflight.py --project PROJECT_DIR`.
Install a missing tool only after the user agrees, saying what it is for. Report
missing browser or account access rather than claiming checks that did not run.

Read `~/.video-edit/profile.md` if it exists (creative defaults, locations, asset
libraries). Open the first reply with one line naming the stored defaults you are
applying (takes, audio source, speed, sound) so the user can correct one instead of
retyping them all. When the user marks an instruction as a habit ("always", "as
usual", "like before") or repeats one from an earlier brief, offer to record it there.

## Brief and scope

Without a brief, ask once for what the footage can't tell you: where it will be
posted, rough length, music, effects or a hook headline, whether they need an
editable Resolve project, and recordings of their own product or data when claims
depend on them.

Current instructions override stored defaults; scope a preference to the projects it
was meant for. Honor staged scope (restate the brief, wait for uploads, cut dialogue
only, collect assets first) when that is what was asked; otherwise continue
authorized work without adding approval stops. Preserve originals and prior
deliverables, and keep derived assets local until upload is authorized. Check
platform length, caption, watermark and ranking claims against current official
sources when they affect the task.

- Resolve assembly, speed, rendering or console recovery: [Resolve](references/resolve.md).
- FFmpeg rendering, transcription, audio recovery and sync, mixing, captions and
  timing: [technical reference](references/technical.md).
- Publishing or scheduling, only when requested: [publish](references/publish.md).
- A requested reflection: [reflection protocol](references/reflection.md).

## Recover the project and active brief

Reuse the existing project's preprocessing, scripts and checked assets before
building anything.

Keep the active brief in the project so nothing regresses between versions: the
latest requested version and every outstanding correction, until each is verified in
an export. A later speed or ending request replaces the older one; unrelated accepted
edits stay. A user timestamp points into the version they watched: find the words
there, then map back to the source. Rejected assets and treatments stay rejected,
including under a new crop or in a later scene.

Long encodes fail on storage, rotation and HDR: probe those first and prove framing
and color on a short sample. A low-resolution review copy never replaces camera
media in the final.

## Choose the style

Choose from the footage, the goal and any reference. [Styles](styles/README.md)
indexes the packs (talking head, skit and meme, screen demo, reel recreation) and how
to mix styles in one video. A pack is a head start: the brief and profile override
it, and a style without a pack is built from the same layers. To recreate a posted
reel, start with the [recreation pack](styles/recreation/README.md).

## Cut the speech

When speech carries the edit:

- Transcribe locally once and cache the word timestamps
  ([commands and fallbacks](references/technical.md#probe-and-transcribe)).
- A spoken rejection ("cut that", "forget that") removes the abandoned delivery from
  every section; find its restart from context, not a fixed number of seconds.
- Use the most fluent, complete delivery of each passage, ordered by story meaning
  rather than recording order. The script is an outline, not a word list, but keep
  the setup, transitions and ending the story's logic needs. When the user says
  fluent takes exist, search the rest of the source before proposing omissions or
  pickups. If the source ends before the story does, say so.
- Start on the first complete intended word, trim script-reading lead-ins and tails,
  and keep natural breaths and soft consonants. On camera, takes start and end with
  eyes on the lens. Prefer another complete take over a chain of word repairs; cover
  an unavoidable glance with a moving split edit or a relevant full-frame insert.
  Never freeze a face or fabricate delivery to hide a bad cut.
- Whole-clip ASR merges a false start with its restart, and long ASR drops repeated
  words at joins. Run `scripts/restart_scan.py AUDIO CUTLIST.json` before the first
  render, and check every join with overlapping short windows that cover the outgoing
  tail and the incoming phrase ([details](references/technical.md#repeated-speech-checks)).
  Say whether you listened; ASR and frames are not listening.

The normal-speed cutlist is the timing authority; playback speed is a separate
setting.

## Source and build assets

What to source, and how much, comes from the style pack and the brief.

- Search the asset library first when the asset-library skill is installed, ingest
  new picks with provenance, and register only what another project is about to reuse.
  Without it, keep a [project manifest](references/technical.md#reusable-media-library).
- Keep each placed asset's source and credit, and verify a source's context before
  using it as evidence.
- Prove a treatment on its hardest passage (the hook, the busiest frame, the
  trickiest gesture) before building the whole set. That is your check, not an
  approval stop; reuse an accepted treatment without asking again.
- When sourcing is delegated, one editor still owns the timeline and the cue sheet.
- Generated imagery is an option when it explains a beat better than anything real;
  inspect one before paying for more.
- An animated or 3D shot built in code goes to the animated-video skill as a shot
  brief (frame range in the normal-speed cutlist, fps, size, cue words with their
  frames, layer order, approved look). Place the clip and sound events it returns and
  add its library entries to this cut's declaration. When the deliverable is an
  animated film with a camera insert, animated-video owns the timeline.

## Assemble, finish and revise

Build a native Resolve timeline with separate camera, visual, caption and
mastered-audio tracks when the brief or profile wants an editable project and Resolve
is operable here ([setup](references/resolve.md#set-up)). Otherwise render with
FFmpeg and say there is no editable project. A flattened movie imported into Resolve
is not a native composition.

- Color: keep the camera's look. Diagnose rotation and HDR before adjusting, and use
  one technical HDR-to-SDR conversion when needed. Grades, brightened backgrounds and
  blur are opt-in.
- Text: follow the pack. Keep copy editable (caption data plus an SRT, or the build
  script), spell names right, and use the user's exact words for supplied copy.
  Make standalone lines (a hook, headline, skit caption or cover) as short as the idea
  allows; a longer line is fine when the point needs it. On text with no background,
  put the word or number that carries the point on a filled color box, and choose both
  the box color and that word's color against the scene rather than one fixed pair
  ([text_overlay.py](scripts/text_overlay.py) `--style highlight` with `--accent` and
  `--accent-ink`). Text that already sits on a background, such as white line boxes,
  needs no second color.
  Captions never paper over wrong spoken words. Translate foreign speech for the
  audience without inventing emotion.
- Sound: speech dominant with measured peak headroom. Add music or effects when the
  brief calls for them, and prove each audible in an exported test under speech and
  in pauses; file presence and whole-mix loudness prove nothing. Keep one cue sheet
  for the video even when beats are built in parallel, and count uses per file before
  rendering: per-beat quotas multiply into clutter. Effects come from the asset
  library, the profile's libraries and the bundled
  [sound-effect library](assets/sfx/README.md); read its rights note before
  publishing. Plan music credits when choosing the track.
- Revisions change the cutlist, manifest or native timeline, not a copied pipeline.
  Ripple every dependent layer after a cut. Apply a speed change once to linked
  picture, audio and every timed layer, preserving pitch, and update visible
  playback-rate labels on sourced demos. Derive final caption and visual intervals
  from the frame-rounded result and clamp them to its end. A visual-only revision
  replaces only the affected layers and keeps the accepted mix
  ([procedure](references/resolve.md#visual-only-revisions)).

Stills at cue frames catch layout problems at a fraction of a full render's cost;
full renders are for what stills cannot show.

## Verify the exact deliverable

Editorial and technical evidence answer different questions.

- Editorial: judge against the pack's quality bar, with contextual playback when
  available. User feedback outranks a contact sheet or a transcript as evidence of
  taste.
- Technical: on the exported file, re-check everything the change could have
  touched (decode, geometry, duration, linked speed, levels and peaks, caption timing,
  changed joins, the brief's visual constraints). Reuse evidence only for what is
  provably unchanged; for audio that means identical decoded PCM. Use a check that
  tests the reported defect; a similarity score with an arbitrary threshold is not one.
- On camera, check eyeline on the export: a face-size strip of each on-camera shot's
  first and last half second and its middle. Thumbnail contact sheets hide where the
  eyes are.
- After a cut, speed or mix change, re-transcribe the final mixed audio into a
  separate QA file and check changed joins with overlapping windows. A correction is
  verified only when the check covers its full context, including the next clip.

Deliver one unmistakably named current file, the native project when there is one,
and a short change summary. A DRP references local media; it is not an archive.
Record the cut: with the asset-library skill, declare the exact files placed and
their uses; without it, the project manifest is the record. Report delivery and
catalog status separately; a blocked catalog step does not hold back the file.

## Maintain the skill

On a requested reflection, follow the [reflection protocol](references/reflection.md).
A lesson belongs in this file only if it is right for every edit; craft for one style
goes to its pack, and personal taste to `~/.video-edit/profile.md`.
