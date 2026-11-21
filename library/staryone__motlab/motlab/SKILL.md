---
name: motlab
description: Make and edit videos as code with the motlab engine, with no AI video or image generation: product and app ads, logo animations, explainers, tutorials, screen-recording and footage edits, social clips. The agent builds every scene from the user's references and opens the motlab viewer; the user leaves notes there and exports the video. Use whenever someone asks for a video, animation, motion ad, promo, explainer, reel or short, mentions motlab, or gives notes on one.
---

# motlab

Build a video as code and put it in the motlab viewer, where the user plays it, steps through it frame by frame and
points at what to change. Everything is code, so a note such as "slower here" means changing a number and reloading.
No AI model makes any picture or video.

**The split of work.** The user gives a folder of high-quality references (pictures, logos, screenshots, footage,
fonts, music, voiceover, sound effects) and their direction. You do everything up to the render: it redraws and
animates what is in the references, edits the footage, plans the shots, builds every scene, places the sound and
revises from the user's notes. The user reviews in the viewer and renders. Good references in, good video out. If a
reference is too small, blurry or missing, ask for a better one rather than inventing it.

**The first thing the user sees is the real video.** No rough storyboard, animatic or approval step before building.
Plan the shots, build all of them properly, and open the viewer. The review happens on the real scenes.

**You never render the video.** Don't run `motlab render` or `motlab video` on the project, and don't offer to.
When the user is happy, they press Export in the viewer and pick a resolution. `motlab stills` (single frames to check
your own work) and `motlab events` are fine. Render only if the user asks for it in chat in so many words.

## The engine

`motlab` is a command on PATH. Run `motlab --help` once at the start: it lists the commands and prints the engine
folder (its README, the `example/` project and `src/page/footage.js`).

If `motlab` is not found, ask the user how they installed it. From npm (`npm install -g @motlab/cli`), run
`npx @motlab/cli setup --skill none`; it adds the command when npm's folder is not on PATH. From a clone (the
folder with `install.js` and `bin/motlab.js`), run `node install.js --skill none` there; it puts the command on PATH.
If they have neither, follow `docs/install-for-agents.md` from https://github.com/staryone/motlab. Until the command is on PATH, call
`node <engine>/bin/motlab.js`. Never hard-code the engine path anywhere else. If a render or still fails because Chrome
or ffmpeg is missing, run `motlab doctor` and show the user what it reports. When the user asks to update motlab or
its skills, run `motlab update`. For an npm install it prints the two commands that update it; run them if the user
agrees. If it stops because the engine folder has local changes or commits of its own, show the user its message and
ask; never stash, reset or discard their changes. The new skills load in a new session.

## The workflow

1. **Brief and references.** Ask what the video is for, where it will be seen, how long it should be, whether it
   needs a voiceover, and the **orientation**: landscape 16:9 (1920x1080 pages), portrait 9:16 (1080x1920) or square
   1:1 (1080x1080). Then go through the user's folder:
   - List everything. Measure images (`python3 -c "from PIL import Image; ..."` or `ffprobe`), probe footage and audio
     with `ffprobe` (size, frame rate, rotation, length, audio track), and note the music's length and tempo.
   - Check resolution against how close the camera will get. Ask for better files or rebuild as vector shapes. Get logos
     as real files: one cut from a screenshot or redrawn from memory is only acceptable if the user says so and checks it.
   - If the user has an asset kit (made with the motlab-assets skill: a folder with `kit.json`, `style.md` and
     `tokens.json`), copy it into `<video>/assets/kits/<name>/`, read its `style.md` and `tokens.json` before planning, and
     use its assets and colours rather than drawing new ones. New assets the video needs belong in the kit, through that
     skill.
   - Read any brand guidelines. Use the brand's fonts if they are there; otherwise pick any Google Font that fits the
     video's vibe (`references/fonts.md`).
   - Decide the style: the ad preset (`references/style-rules.md`) for product, app and brand ads, or when the user asks
     for it; otherwise the references set the look, and `references/craft.md` applies to everything.
2. **Know where it ends.** Find out what the viewer is meant to do afterwards (download, visit, sign up) or which shot
   the video hands over to, and plan the end from there.
3. **Plan the shots.** Number them (5 to 10 for a short piece, more for longer edits) and give each a duration (on the
   music's phrases, if the music is there already), what is on screen, what moves, and how it turns into the next shot. If you cannot say how a
   shot becomes the next one, the transition is a plain cut and the shot needs rethinking (`craft.md` §9). Post the list
   in chat in a few lines so the user knows what is coming, then go straight on to building. Don't wait for approval.
4. **Build every scene.** Write the real scenes in `<video>/scenes/` and list them in `<video>/project.json`. Keep the page contract (below). Keep all of a page's beat times together in one
   constant near the top, so changing the timing means editing one place. Footage goes in as a layer (`references/footage.md`). Copy templates and scripts from this skill's
   folder next to the scenes as needed. Every scene is finished work, built to `craft.md` (and the preset, if on): no
   placeholder frames, rough sketches or shots left for later.
5. **Sound, now or later.** Music and effects can come after the picture. The first build may be silent, or carry
   only the music if the user already gave it. When music arrives later, re-time the shots to its phrases if the user
   wants that. Build the effects mix with `mix.py` from the pages' `EVENTS` (`references/sound-and-music.md`), save it
   in `<video>/audio/`, and list it in `project.json` with the music, voiceover and any footage sound, so the viewer
   plays it and Export includes it.
6. **Check stills yourself.** `motlab stills <page> <outDir> 0.5 1.2 …` (it serves the folder with `project.json`, so
   the page can load files from the whole project), then `python3 scripts/contact_sheet.py <outDir> sheet.jpg` and look at it. Look
   inside every transition at three or four moments as well as at the still parts, and put the references next to the
   stills: a wrong shape, a flipped layout or parts that pass through each other are easy to miss otherwise. Fix what `craft.md` would flag
   before the user sees it.
7. **Open the viewer.** Run `motlab edit <video>`; it ends at once and prints the address. Give it to the user. Say in
   a few lines what is in it and what you could not check: you saw stills, not playback, and you cannot hear the sound. Give the
   user the "listen by ear" moments `mix.py` printed.
8. **Revision rounds.** The user plays the video, steps through it frame by frame, clicks the spot and comments, or
   leaves notes in the viewer and says "kerjakan semua catatan". When they say "this one", "here", "yang ini" or "di
   sini", or mention notes, read `<video>/selection.json` first (and look at `<video>/selection/<n>.png` for each note
   with a box or point), then grab that frame with
   `motlab stills <scene> <dir> <frame time>` (see below) so you see what they see. Apply every open note, check stills
   around the change, re-run `mix.py` if beats moved, and tell the user to reload. Report what changed in plain words.
   Before a round that changes a lot, copy `scenes/` to `backup/<n>/`. Never delete or edit the user's reference files.
   Many rounds are normal; keep going until the user is happy.
9. **The render is the user's.** They press Export in the viewer and pick 720p, 1080p, 1440p or 4K. The file lands in
   `<video>/out/<folder>-<resolution>.mp4` (4K as `-2160p`). To look at an export they ask about, tile one frame a
   second into a single image: `ffmpeg -i out.mp4 -vf "fps=1,scale=480:-1,tile=6x10" -frames:v 1 sheet.jpg`.

**Paid tools:** generating a voice, music or anything else on a paid service (ElevenLabs, Suno and the like) spends the
user's credits. Do it only when they ask.

## Project layout

One folder per video. The user's references can stay where they are if they are inside this folder; anything used from
outside it is copied into `assets/` (copy, never move), because the viewer and renderer only serve the project folder.

```
promo/
  refs/                 the user's references, untouched
  assets/               copies, cut-outs, rebuilt vectors, fonts
  footage/              video clips used in scenes
  audio/                music, voiceover, the effects mix
  project.json          the video
  scenes/               one page per scene
  backup/               copies of scenes/ before big revision rounds
  out/                  the user's exports
```

`project.json`:

```json
{
  "fps": 30,
  "scenes": ["scenes/01-hook.html", "scenes/02-feature.html"],
  "audio": [
    { "file": "audio/music.wav", "start": 0, "volume": 0.6 },
    { "file": "audio/sfx.wav", "start": 0, "volume": 1 },
    { "file": "footage/demo.mp4", "start": 4.0, "from": 12.5, "duration": 6 }
  ]
}
```

- Scenes play in list order and each lasts its page's `TOTAL`. All scenes need the same canvas size, which sets the
  orientation of the whole video. The join between scenes is a hard cut, exact to the frame. For a move that carries
  across it, the next scene's `t = 0` must show what the previous scene would show at its `TOTAL`, one frame after its
  last frame. Repeating the same picture holds for a frame and stutters. Use one scene per shot or beat, so the viewer
  and `selection.json` point at it; keep a long continuous move (one camera, shapes morphing through several beats)
  inside a single page.
- A scene can instead be `{ "file": "scenes/02.html", "transition": { "type": "crosswarp", "duration": 0.5 } }`: the
  scene before turns into it through a shader, and the two overlap for that long, so it starts that much earlier and
  the video is that much shorter. Use these for edits, explainers and talking heads; in an ad, a shape that carries
  across the cut (`craft.md`) is still better. The types and options are in `references/motion-and-libraries.md`.
- `audio` is mixed by ffmpeg. `start` is seconds from the start of the whole video, `volume` a multiplier, `from` and
  `duration` pick a part of the file. A video file listed here contributes its sound.
- `window.EVENTS` times are per scene. To place a sound on a beat, add the scene's start (the `TOTAL`s before it,
  minus the transition durations up to and including this scene's own).
- Another `.json` file in the folder with a `scenes` list is a version with the same assets, for example
  `project-tiktok.json` for a cut without the affiliate part. The viewer's header has a version menu, and the user can
  make a version there ("New version from this one", in Indonesian "Versi baru dari ini", copies the open one to `project-<name>.json`). When the user asks for a
  version or a revision ("revisi 2"), copy the current project file to `project-<name>.json` and change the copy. A
  scene that has to differ in one version gets its own copy (`scenes/05-cta-tiktok.html`) listed only there; never
  change a shared scene for one version. `selection.json` says which version a note is about (`project`), so edit that
  file. Export writes `out/<folder>-<name>-<resolution>.mp4`.
- `motlab edit <video>` (or a project file) opens the project in the viewer at `http://127.0.0.1:4173/p/<folder>/`,
  starting the viewer in the background when none is running, prints the address and ends. Give the user the address
  it prints. `motlab restart` restarts the viewer (after `motlab update`), `motlab stop` ends it. The project name in the header switches between projects. It cannot edit; the
  user reloads after changes. Space plays, arrows step frames on the timeline, Ctrl+scroll or `+`/`-` zooms the
  timeline, Export renders 720p to 4K.
- A click writes `<video>/selection.json`:

  ```json
  { "project": "project.json", "time": 4.094, "scene": "scenes/02-feature.html", "sceneIndex": 2, "sceneTime": 1.094,
    "frame": 32, "audio": null, "range": null, "marks": [] }
  ```

  The times are where the click landed, not snapped to a frame. `frame` is the frame of that scene the preview shows
  (`floor(sceneTime * fps)`, the same grid as the render), so pass `frame / fps` to `motlab stills` to see exactly that
  picture. Older selections have no `frame`; compute it the same way. Inside a scene transition, `transition` is
  `{ type, from, frame, frames }` and the note is about the transition (`from` is the scene it comes from); `scene` is
  the one it leads into, and stills of either page alone will not show the mix, so check it in the viewer.
- `range` is `{ start, end, scenes }` when the user marked a stretch of time on the timeline (the range button or `R`, Shift+drag, `X` for a scene, or `I` and
  `O`): video seconds on the frame grid and the scene numbers it covers. A note like "ini terlalu lambat" with a range
  is about that whole stretch, not the single `time`.
- `marks` are the user's notes, numbered `n` across all versions of the folder: `{ n, id, note, time, scene, sceneIndex,
  sceneTime, frame, transition, box, point, range, image, project }`. Each is a box or a point drawn on one frame, or
  a range, with the text `note` saying what is wrong there (it can be empty: then the spot is the note). `box` and
  `point` are in the scene's own pixels at `?scale=1`, the same units as the scene code. `image` is
  `<video>/selection/<n>.png`: that frame with the note's box or point and number drawn on it. Look at it first, then
  find what the scene draws inside the box. It is the preview, not a clean still, so use `motlab stills` for a clean
  frame. Work only on the notes whose `project` is the version you are editing, and when the user says "catatan 3",
  that is `n: 3`. Skip notes with `"done": true`; they were dealt with in an earlier round. Report per note number
  what you changed, and once a note is applied and checked in stills, set `"done": true` on that mark in
  `selection.json`. Change nothing else in that file: the viewer writes it, and it keeps your `done` while it is open.
  The user opens a note again in the viewer when the fix was not right. `time` is on the same clock as `start` in `project.json`, so a sound effect for that moment
  gets `"start": <time>` (or the frame's time, for a hit on the frame). `audio` holds `{ file, start, index }` for a
  click on an audio clip; the point inside that file is `time - start + from` (`from` from the entry in
  `project.json`). When the user says "this one", "here", "yang ini" or "di sini", read this file first and act on that project,
  scene and time.

The engine folder's `example/` is a small working project (three scenes, music, three sound effects) to copy from.

## Page contract

- `<canvas id="c">` sized `W * scale` by `H * scale` with even dimensions, where `scale` comes from `?scale=`
  (1 in the viewer, 2 for a 4K render of a 1920x1080 page)
- `window.renderAt(t)` draws the frame at `t` seconds and may be async
- `window.TOTAL` is the length in seconds
- `window.ready` is a promise that resolves when fonts and assets are loaded. Set it before any `await` in a module
- `window.EVENTS` (optional) is `[{ name, t }]` for syncing sound
- `?t=` draws a still

Frame `f` is rendered at `t = f / fps`. The same page runs in the viewer, so what the user plays is what renders.

## Choosing how to build it

| Approach | Use it for | Tools |
|---|---|---|
| 2D canvas | Flat brand animation, kinetic type, explainers, captions, edits | `templates/template-2d.html`; illustrations: `references/engine-2d-puppet.md` |
| UI in 3D space | Apps and software: real screenshots as panels with a camera and depth of field | `templates/template-3d.html`, `scripts/gl3d.js`, `references/engine-3d.md` |
| three.js | Real 3D objects that turn: a product, character or logo from a GLB or glTF file, or built from shapes | `templates/template-three.html`, `references/engine-3d.md` |
| p5.js | Generative graphics: noise fields, particles, patterns, data drawn as shapes | `templates/template-p5.html`, `references/engine-p5.md` |
| Footage | Screen recordings, camera clips, tutorials, reels made from real video | `references/footage.md`; jump cuts in a talking head: `scripts/cut_pauses.py` and `/__motlab/cuts.js` |
| Blender | Photoreal products or a filmed studio look. Slower, and Blender must be installed | `scripts/blender/`, `references/blender.md` |

Mix them freely: footage with 2D captions, a 3D UI shot that ends on a recording, a Blender product over a canvas end card.

## Kinds of video

- **Product, app and brand ads (8 to 20 s).** Turn on the ad preset. One journey in 5 to 10 beats, every shot morphs
  into the next, a clear call to action.
- **Animated pieces and logo animations.** The references set the style. `craft.md` still applies: shapes that carry
  across transitions, one-way camera moves, nothing dead still.
- **Explainers.** One scene per idea. Write the voiceover or on-screen text first and time the scenes to it.
- **Tutorials and screen-recording edits.** Cut the recording into shots, zoom into the part being explained, highlight
  the control being used, add short captions. Slower pacing: text stays up long enough to read twice, and legibility
  beats "always moving" or "keep it centred".
- **Edits of camera footage.** Trim, order and time clips to the music, add titles and overlays, use the clips' own
  sound where it matters. Hard cuts are fine here; match cuts and motion-led cuts are better.
- **Portrait and square social clips.** Same workflow on a 1080x1920 or 1080x1080 canvas. Keep text and faces clear of
  the top and bottom of the frame, where the app's own interface sits. Hook in the first second.
- **Long videos.** A 10-minute test render at 4K took about 19 minutes on the test laptop and made a 3.2 GB file, and
  a real 2-minute video has been exported at 4K. Suggest a 1080p export first for a long video, and say how long 4K will take.

Transparent (alpha) output is not available yet.

## Keep it above board

Before the video is shared, settle these with the user:

- **Brands.** The brand has to be the user's, or one they have permission to promote. For any other brand the video is
  a spec piece, for practice or a portfolio: it ends on a small "Spec ad. Not affiliated with <brand>." line, does not
  copy the brand's actual campaigns or pose as official, and is never bought as ad space.
- **Assets.** Every file in the video (footage, images, fonts, sounds, music, 3D models) is either the user's own or
  covered by a licence that allows this use.
- **Claims.** What the video shows or says has to be true, and the user has to be able to back it up. Nothing that
  promises earnings or results, and no made-up numbers, reviews, ratings or awards.
- **Privacy.** Personal details in screenshots and footage are blurred or swapped out, and anyone recognisable has
  agreed to appear.

## Where to read more

| When you are… | Read |
|---|---|
| making anything look polished: transitions, camera, easing, text, assets | `references/craft.md` |
| making a product, app or brand ad (the ad preset) | `references/style-rules.md` |
| editing screen recordings or camera footage | `references/footage.md` |
| screens and cards floating in 3D, or real models with three.js | `references/engine-3d.md` |
| making generative graphics with p5.js | `references/engine-p5.md` |
| cutting out, splitting or puppeting flat illustrations | `references/engine-2d-puppet.md` |
| choosing, downloading and loading fonts | `references/fonts.md` |
| rendering a product in Blender, shaded or in the flat look | `references/blender.md` |
| ending an animation on real footage | `references/into-footage.md` |
| sound effects, a voiceover or music | `references/sound-and-music.md` |
| easing, springs, motion blur, transitions between scenes, GSAP, Anime.js, Lottie or Theatre.js | `references/motion-and-libraries.md` |
| a frame looks wrong or a render misbehaves | `references/pitfalls.md` |

## Setup

Needs the motlab engine (see "The engine"), Node 24 or newer, Python 3 with Pillow, numpy and scipy,
ffmpeg and ffprobe on PATH, and Google Chrome (set `CHROME` if it isn't found). Blender only for the Blender approach.
Commands in this skill say `python3`; on Windows use `python`. Check these first, and tell the user what is missing
and how to install it before you start.

## Scripts and templates

- The engine: `motlab stills` to check frames, `motlab events` to dump the beat list, `motlab edit` for the viewer.
  `motlab render` and `motlab video` are the user's (see the top). Chrome always runs on the GPU.
- `templates/template-2d.html`, `template-3d.html` (gl3d.js), `template-three.html` and `template-p5.html`: starting
  points for scenes. The three.js and p5.js templates load their library from a CDN, so they need the network.
- `contact_sheet.py`: puts the stills from `motlab stills` on one sheet, labelled with their times.
- `key.py` removes a flat background, `split.py` cuts a cut-out into layers, `grid.py` overlays pixel coordinates.
- `gl3d.js` places 2D-canvas panels in 3D; `puppet.js` bends a cut-out with pins.
- `get_font.py`: searches the Google Fonts catalog and downloads a family into the project. `templates/font-specimen.html`
  shows the downloaded fonts side by side for `motlab stills`.
- In every scene page: `/__motlab/motion.js` (easings, `cubicBezier`, `spring`, `tween`, `stagger`, `motionBlur`),
  `/__motlab/footage.js` (video files) and `/__motlab/cuts.js` (a cut list over one recording).
- `cut_pauses.py`: cuts the pauses out of a talking-head recording into `cuts.json`, and with `--audio-out` writes the
  voice with the same cuts.
- `mix.py`: puts library sounds on the page's events at a level set by their role, lowers them under a voiceover,
  reports how close each landed and which moments to listen to. `synth_sfx.py`: builds a free sound kit. `get_sfx.py`: finds openly licensed sounds on
  Openverse and downloads them with a `CREDITS.md`. If the user has earshot (`earshot --help` runs, or its MCP tools
  are listed), use it to pick sounds and measure the mix (`references/sound-and-music.md`).
- `blender/`: `kit.py` (scene, light, camera and render helpers), `tracks.py` (move curves), `mesh_from_sdf.py`
  (meshes from distance functions) and `example_scene.py`, a complete scene to start from.
- `compose_into_clip.py`: joins transparent PNG frames from a Blender render to a real clip, so the render hands over
  to the footage (`references/into-footage.md`).
