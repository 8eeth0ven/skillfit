---
name: code-loop
description: Make a seamless, perfectly looping generative video in code, from a three.js scene or a raw GLSL fragment shader, rendered frame-perfect with jittered anti-aliasing and motion blur, then checked for a visible seam, freezing and blinking. Use when asked for a "seamless loop", a "perfect loop", "generative art video", a "shader loop", "three.js animation to video", to "render a looping animation", a looping GIF from code, or any code-driven animation that has to loop without a visible cut.
---

# Code loop

A loop is seamless only if the frame after the last frame is exactly the first frame, and every motion keeps its speed across that point. The way to get that is to make every frame a pure function of the loop phase, built from motions that complete a whole number of cycles per loop. Then render each frame as an average of many slightly shifted renders, which gives clean edges and real motion blur, and check the result with numbers instead of by eye.

## Quick start

```
mkdir -p loop && cd loop
printf '{"type":"module"}' > package.json && npm i three@0.170.0 playwright@1.60.0
S=<path to this skill>
cp $S/templates/three_starter.html scene.html     # or shader_starter.html for a raw GLSL loop
cp $S/scripts/render_loop.mjs $S/scripts/check_loop.py .
node render_loop.mjs scene.html loop.mp4 --stills=0,2,4,6     # full-quality stills in stills/
node render_loop.mjs scene.html preview.mp4 --preview         # whole loop, half size, 30 fps, seconds to a minute
node render_loop.mjs scene.html final.mp4 --gif               # 60 fps, 8+ samples a frame, plus a GIF
python3 check_loop.py final.mp4 --heat blink.png              # seam, freezes, blinking
```

Set `$FFMPEG` if ffmpeg is not on the PATH. Sizes: `--size=1920x1080` (default), `1080x1920`, `1080x1080`, `1080x1350`. `--loops=3` repeats the loop in the mp4. If a long render is interrupted, run the same command again with `--resume`.

## The page contract

Both starters implement it. Any page that does can be rendered by `render_loop.mjs`.

| Hook | What it does |
|---|---|
| `window.LOOP` | Loop length in ms. The renderer renders exactly one loop by default. |
| `window.READY` | Set (or a promise that resolves) once assets, fonts and shaders are ready. |
| `window.render(ms)` | Draws the frame at time `ms`. |
| `window.renderMany([[ms, jx, jy], ...])` | Draws each sub-frame into a float buffer with additive blending at weight 1/n, then tone maps once to the canvas. One screenshot per frame leaves the browser. |
| `window.setJitter(x, y)` | Sub-pixel offset in canvas pixels. In three.js, add `2x/width` and `2y/height` to `projectionMatrix.elements[8]` and `[9]`. In a shader, add it to `gl_FragCoord.xy`. |
| `window.probe(ms)` | Optional. Screen positions `[x, y, ndcZ]` in output pixels of a few points that move. The renderer uses it to decide how many motion blur samples each frame needs. |
| `?w=&h=&scale=` | Output size, and a render scale for previews. |

## The rules of a seamless loop

1. **Everything is a pure function of the phase** `p = ms / LOOP`. No `Date.now()`, no `requestAnimationFrame` deltas, no state carried from the last frame, no `Math.random()` at render time. Seed every random generator, so the preview and the final build the same scene.
2. **Every periodic motion has a whole number of cycles per loop:** `sin(2π·k·p)` with integer `k`. A rotation turns `k` full turns, or a whole number of symmetry steps (a 4-fold grid only needs a quarter turn). A texture scrolls a whole number of its widths. A walk cycle repeats a whole number of times.
3. **Loop noise by walking a circle through it.** Sample `noise(x, y, R·cos 2πp, R·sin 2πp)` with 4D noise (or 3D noise for a 1D field). The radius `R` sets how much it changes over the loop. Adding `p` to a noise coordinate never loops.
4. **Easing must end where it starts.** Use moves that go out and come back (`0.5 - 0.5·cos 2πp`), or keyframes whose last key equals the first, interpolated with a curve that also matches speed at the wrap (a periodic spline). A plain ease-in-out that stops at the seam reads as a hitch.
5. **Do not wrap `ms` with `%` in the page.** Periodic maths does not need it, and leaving it unwrapped lets the exact seam test prove the loop is periodic. Wrap only the lookup inside a keyframe track.
6. **The loop length must be a whole number of frames** at every frame rate you deliver: 60, 30 (platforms often re-encode to 30) and the GIF rate (25 or 20). 4, 6, 8 and 10 seconds all work.

## Why jitter and motion blur

A single render per frame has stair-stepped edges, and thin or distant detail lands on different pixels each frame, so it shimmers and blinks. The renderer instead averages several renders per frame, each shifted by a different sub-pixel offset (a Halton pattern shaped into a tent filter). The same offsets are used every frame, so whatever aliasing is left stays still instead of crawling. When `probe` says things move fast, the renderer adds more samples spread across the shutter time (up to 32), which turns fast motion into a smooth streak instead of a stutter. Previews use one sample, so they shimmer by design. Judge blinking on finals only.

## Craft that decides the quality

- **World-anchored, not screen-anchored.** Hatching, grain, noise textures, dither patterns and haze must be attached to the object or the world. Anything fixed to the screen while the scene moves under it crawls and blinks. The one exception is the output dither, which is below one colour step.
- **Telephoto and z-fighting.** On long lenses the depth buffer runs out of precision. Keep separate surfaces apart (a few cm at 10 m, more at 400 m), push `near` out as far as possible, and paint markings onto one surface instead of stacking planes.
- **Colour.** Render in linear light into float targets, average there, then tone map, grade and encode to sRGB once at the end. Averaging after sRGB encoding makes blur and anti-aliased edges too dark. Both starters use the Khronos PBR Neutral tone map, a light grade, a vignette and a fixed dither against banding.
- **Speed.** Merge static meshes by material at load (`mergeStatic` in the three starter), and use instancing for many copies. Draw calls, not triangles, are usually the limit.

## Workflow

1. **Stills** at 4 to 6 phases with `--stills`. Fix composition, colour and detail here, where each try takes seconds.
2. **Preview** with `--preview` and watch it on loop. Fix timing and motion here.
3. **Final** at full quality. Only once the preview is approved.
4. **Check** with `check_loop.py`. It must say PASS. Look at `blink.png` if anything blinks.

## Sharing

| Where | Size | Notes |
|---|---|---|
| X | 1920x1080 or 1080x1080 | 60 fps is kept. Short clips loop automatically. GIFs up to 15 MB. |
| Instagram feed | 1080x1350 (4:5) | May be re-encoded to 30 fps. Use `--loops` so the post is at least a few seconds long. |
| Reels, TikTok, Shorts | 1080x1920 | Keep the subject in the middle, away from the top and bottom fifth, where captions and buttons sit. |
| GIF | 480 to 720 px wide, 20 or 25 fps | `--gif` writes one with an ordered dither, which stays still between frames and compresses better than error diffusion. |

Fine grain and noise compress badly and turn to mush after a platform re-encode, so keep large smooth shapes and strong contrast.

## Building on this engine

[perspective-illusion](../perspective-illusion/SKILL.md) is one style built on this engine: a telephoto line-art scene with dolly zooms, multi-pass ink lines and a scripted camera. Its templates use an earlier form of the same page contract, without `window.LOOP` and `?w=&h=`, and its `render_fast.mjs` is the ancestor of `render_loop.mjs`.

Details on each topic, more looping techniques and troubleshooting are in [reference.md](reference.md).
