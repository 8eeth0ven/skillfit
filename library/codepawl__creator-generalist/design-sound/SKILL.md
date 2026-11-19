---
name: design-sound
description: "Make, find, choose and mix SFX and music for a video, game or reel: search the sound library, fetch real sounds from the web, generate with ElevenLabs or as foley from the picture, fit music to the cut, mix to platform loudness and check every cue. Licences are warned, never blocking. Use automatically for sound design, SFX, foley, soundtrack, mixing."
license: MIT
---

# Design Sound

One library, two ears, two hands. `search.py` finds a sound from a description (CLAP text-to-audio plus tag keywords)
and draws a sheet so you can look before choosing. `fetch_web.py` and `generate_elevenlabs.py` bring in what the
library lacks, `video_foley.py` (or `fal_foley.py` on a busy card) makes foley from a silent film. `foley.py` builds the effects stem from an event
list, `fit_music.py` edits a real track to the cut, `score.py` sketches music (placeholder only), `mix.py` carves,
ducks, masters and checks, `listen.py` checks any WAV. The library is data: `SOUND_LIBRARY_DIR` (default
`Documents/sound-library` in the home folder; `index.json`, `embeddings.npz`, `sources.json`), indexed in place.
Read `local.md` next to this file when it exists: the owner, machine paths and project rules, which win.

## When to use

Any video, reel, episode, game or demo that needs a sound made, chosen, placed, or a mix built or checked; pipelines
that cut and place sounds (Remotion reels, `watch-video` remakes, 2D and 3D films) call these scripts.

## The loop

1. Describe each event in plain words, the way a brief would ("a heavy wooden door shut hard"), plus its kind.
2. `search.py "<description>" --sheet sheet.png` (add `--kind oneshot|bed|music`, `--max-seconds`).
3. Open the sheet and look: a hit has a sharp rise and the energy where you expect; a swell, a hiss or a long tail
   where you wanted a snap means a wrong pick. Read the rows: attack ms, centroid, band shares, licence.
4. Nothing fits: get it (`references/sources.md`). Web first (`fetch_web.py "<query>" --source openverse|archive|
   myinstants|youtube`), ElevenLabs when nothing real fits or the project wants it (`generate_elevenlabs.py sfx|music|
   plan|stems|video-music`; it checks credits first and prints the real cost). `index.py --add <folder>`, back to 2.
5. Design: `events.json` from the sim or timeline into `foley.py` (layered, rotated, panned, sized,
   `references/foley.md`). A silent film with no event list, or too many contacts to place by hand: `video_foley.py`
   (`fal_foley.py` when the card stays busy) first (`references/video-foley.md`); if it reports `heard_nothing`, go back to `foley.py`. Music: a real or
   ElevenLabs track, `fit_music.py` to the cut (`references/music.md`), or a composition plan on the cuts.
6. `mix.py mix.json --out final.wav --sheet sheet.png` (`references/mix.md`, which holds the mixing practice and its
   sources): voice high-passed and de-essed, music ducked (auto-lowered to keep the voice 11 LU over it) and carved
   at 1-4 kHz, beds band-limited, mono bass, -14 LUFS, ceiling lowered until AAC and Opus decodes stay under -0.3 dBTP.
   It listens to each stem alone and reads sync, masking and phone audibility on the final.
7. Fix every flag and rerun the stage that made it: wrong sound, sync over one frame, MASKED, `QUIET UNDER MUSIC`
   (cue under +6 dB(A) over the ducked music), `WEAK ON PHONE`, voice under 10 LU over the music, short-term over
   integrated + 5 LU, mono loss over 3 dB, a `reused` recording. Look at the final sheet: every event shows a front.
8. Report licence warnings once, one line per file, and the CC BY credits. Say plainly that nobody has listened to the
   mix unless someone has: these checks are measurements. For a film, send the owner a fast preview first.

## Commands

`PY` = `uv run --no-project --python 3.12 --with numpy --with scipy --with librosa --with soundfile --with pyloudnorm
--with psutil --with torch --with transformers --with matplotlib python` (CPU torch is enough once indexed).
`NET` = `uv run --no-project --python 3.12 --with numpy --with psutil --with requests python`.
Scripts live in `scripts/` next to this file; run them with absolute paths and never from a source sound folder.

- `PY index.py [--add <folder>]...` index new or changed files; re-derives licence classes every run.
- `PY search.py "<description>" [--n 8] [--kind ...] [--licence any|public|cc0] [--max-seconds X] [--sheet out.png]`
- `NET fetch_web.py "<query>" --source openverse|archive|myinstants|youtube [--n 6] [--max-seconds 30] [--start S]`
- `NET generate_elevenlabs.py credits | sfx "<prompt>" --folder X [--seconds S] [--variants 2] [--loop] |
  plan "<prompt>" --seconds S --out plan.json | music "<prompt>" --folder X --seconds S --instrumental |
  music --plan plan.json --folder X | stems <file> --folder X [--six] | video-music <mp4> --folder X [--separate]`
- `<model venv python> video_foley.py film.mp4 --prompt "<material, object, action>" | --shots s.json --out f.wav` reads
  video + prompt, 9 GB VRAM (machine rules in local.md; prompts: references/video-foley.md); `fal_foley.py` on fal.
- `PY listen.py <wav> [--expect "label@seconds"]... [--window 1.0]`; `PY eval.py` the 30-query search benchmark.
- `PY foley.py events.json --out foley.wav [--report r.csv]` the effects stem (prints licence warnings).
- `PY fit_music.py <track> --duration S [--cues cues.json] --out music.wav` a real track edited to the cut.
- `PY mix.py mix.json --out final.wav [--sheet sheet.png] [--no-listen | --quick]` the mix and every check.
- `PY ab_test.py make mix.json --param hold|cue|unmask --out-dir DIR` blind A/B; `ab_test.py pick DIR <A|B|same>
  --note "<the owner's words>"` writes the pick into `house-defaults.json`.
- `score.py score.json --out music.wav` (numpy scipy soundfile psutil only) a MIDI-style sketch only.

## House rules

- Real recordings first, then generated sound; no synthesised stand-ins when either exists. Any licence is allowed:
  warn about `restricted`, `other` and `unknown` files, never drop them. Credit CC BY authors in the
  post or description (`sources.json`, field `credit`). A project's own sound rule wins.
- Every visible event gets its own sound at its own frame, placed from the event time, within one frame.
- No recording shared between two cues in a scene, and no one merged sound covering several actions; no filler
  sounds that no action makes. Only room tone and ambience run under everything. No reverb unless asked.
- Voice is mixed first, at least 10 LU over the music while it speaks; beds 15 LU under it, in their own band and 6 dB
  or more under the cues in their dominant band.
- Keep the top of the mix soft: cut shrill 2 to 6 kHz build-up (a gentle ASMR feel).
- Water and other wet recordings sit about 10 dB under the music and only start when their shot does.
- Short impacts are CLAP's weak spot: always read the sheet for hits, slams and bursts instead of trusting rank 1.
- Values only ears can set (`house-defaults.json`: duck hold, cue margin, voice unmask) are the owner's call, never
  an agent's. Do not edit them or argue them from measurements. When the owner says the music pumps or an effect is
  buried or too loud, run `ab_test.py make` on that mix, send A and B with the printed question, keep the key hidden,
  and on the owner's letter run `pick` with their words. A new ear-only value goes in that file the same way.
- Generated sound costs credits or GPU time: library and web first, plans are free, never buy credits unasked.

## References

- `references/sources.md` web fetching, ElevenLabs commands and measured costs, prompt writing, the licence policy.
- `references/library.md` index fields, adding a folder, licence classes, search scoring and its limits.
- `references/foley.md` event format, layering rules, query words, size and distance maths, what the owner rejected.
- `references/music.md` the music library, mood search, `fit_music.py`, credits, the `score.json` sketch.
- `references/mix.md` mix.json, carving, ducking, phone bass, the whole-mix checks, mixing practice and Evidence.
- `references/video-foley.md` foley generated from a silent film: install, resources, when it hears nothing, licence.
