---
name: repo-timelapse
description: Turn a git repo's history into a video of the project growing. Files appear as a living treemap coloured by language that grows with the code, glows when touched and fades on delete, with a date, a lines-of-code counter, commit messages typing in as captions and an activity sparkline. 16:9 or 9:16, dark or light. Use when the user says "timelapse of my repo", "visualise git history", "build in public video", "show how the project grew", "animate my commits", or wants a video of a codebase evolving.
---

# Repo timelapse

Two steps: read the history into a JSON file, then render it. Both only read the repo.

```
SK=~/simcraft/skills/video/repo-timelapse
python3 $SK/scripts/extract.py <repo> -o history.json
node $SK/scripts/render.mjs history.json preview.mp4 --preview
node $SK/scripts/render.mjs history.json timelapse.mp4
```

Needs python3, git, node with Playwright (already in the simcraft repo root), and ffmpeg (set `FFMPEG` to use a specific one).

## Steps

1. **Extract and read the report.** `extract.py` prints activity by month, the busiest 30 days, the biggest folders, bulk commits and a suggested duration. Use it to pick the story before rendering anything.

2. **Pick the story.** A whole repo is rarely the best video. Choose one arc and say it in one line, such as "the week I built the MVP" or "how the API folder took over". Narrow with:
   - `--since 2025-03-01 --until 2025-04-01` for a stretch of time,
   - `--path src/api` to film one folder,
   - `--exclude 'docs/**'` when docs, fixtures or generated files dwarf the code.
   Re-run extract after each change and check the report again.

3. **Clean the noise.** Lockfiles, vendored and build folders, minified files and test cassettes are skipped by default. Merge commits are folded into the main line, so line counts stay exact. If the report lists a bulk commit (an import or generated code), exclude its folder unless the import is the story.

4. **Preview.** Render with `--preview` (half size, 30fps, about 10 seconds for a 40-second video) and watch it. Check pacing, that captions are readable, and that the map is not dominated by one folder. For single frames use `--stills 3,12,25`, which writes PNGs into the output folder.

5. **Render the final** without `--preview`. It renders at 1080p and 60fps by default. A 30-second video takes about a minute.

6. **Report** the file path, the range and filters used, and anything excluded.

## Render options

- `--duration 30` sets the length in seconds. Use the suggestion from the report: about 20 seconds for a small repo, 40 to 60 for a big one.
- `--vertical` renders 1080x1920 for Reels, TikTok and Shorts. `--size 2560x1440` sets any size.
- `--theme light` switches to the light theme. Dark is the default.
- `--highlight src/api` dims everything outside that folder and shows its line count.
- `--title "My app"`, `--subtitle "..."`, `--end-text "part 2 next week"` change the cards. `--no-title` and `--no-end` remove them.
- `--grow fill` keeps the map full size from the first commit. The default `area` makes it grow with the code.
- `--fps 30` halves render time.

Extract options: `--anonymize` (Contributor 1, 2, ...), `--rev main`, `--name`, `--max-events 1500`, `--include-default-noise`.

## Pacing

- Quiet weeks are compressed automatically. Busy days get more screen time than empty ones, but a long pause never stops the video.
- Captions change at most about once a second. When several commits land close together, the most descriptive message is shown, so "wip" and "fix" rarely appear.
- Fewer than 10 commits makes a thin video. Pick a repo or range with at least 30.

## Posting

- The video opens on a title card, so put the hook in the post text: the final line count or the arc. For Reels, `--no-title` starts the motion in the first frame.
- For 9:16, the layout already keeps the top 150px and bottom 380px clear of platform buttons. Put your own text caption above the video in the editor, not over the map.
- Add a stacked caption in the post that names the arc, such as "60 days of building X, every commit".
- Anonymise authors for repos with other people's names in them, and check commit messages in the preview for anything private before posting.

How it works, the data format and the known limits: [reference.md](reference.md).
