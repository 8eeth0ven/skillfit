---
name: asset-library
description: >-
  Keep a persistent local library of reusable video-production assets across projects: footage,
  images, music, sound effects, characters, animation code and 3D sets. Use when searching for an
  existing asset before sourcing or building one, registering something another project is about
  to reuse, recording which assets a cut used, or checking a project's catalog at delivery.
---

# Asset library

One SQLite database plus the files it points at, under one library root: the record of every reusable asset, each version of it, and every cut it appeared in. The files stay on disk where agents and editors open them.

`LIB` below means `python3 SKILL_DIR/scripts/library.py` (`SKILL_DIR` is this skill's folder; Python 3.9+, FFmpeg). `LIB --help` lists the commands, and `LIB COMMAND --help` gives each one's flags with an example. Every command prints JSON and exits 1 with an `error` and a `hint`.

Two words carry the records:

- **Original**: one source work. A crop, re-encode or ducked mix is a variant of the same original (`--work-id`, `--variant-role`), so reuse limits count originals, not files.
- **Version**: one immutable state of an asset. A media file's version is its content hash. A character, code kit or 3D set is a **bundle**, and each registration snapshots a version of it. A use names the version actually placed, never "latest".

## Set up

Read `~/.asset-library/profile.md` if it exists: it names the root, any local adapter to call instead of `LIB`, and the user's reuse rules. Run `LIB check`. With no library, ask once where it should live (a folder beside the user's video projects is a good default), run `LIB init ROOT`, and offer to write ``Root: `ROOT` `` into the profile.

## 1. Search before sourcing or building

Search by what the viewer sees or hears, not by the project's topic:

```sh
LIB search "keyboard typing" --kind sfx --max-duration 0.5 --unused-in PROJECT
LIB show ID
```

`show` gives where the asset already appeared, the user's opinion in their words, its rights and its versions. Reuse a version as is (copy its snapshot from `bundles/ID/VERSION/files/`), restyle it (its use names the version you started from, with `--modified`), or build new. Reading an old bundle or project for its mechanics is always fine. An asset with unknown rights stays a candidate until the user decides.

## 2. Ingest media when it becomes a candidate

Run `LIB ingest FILE --kind … --source-url … --creator … --license …` while the provenance is still known. Ingest hashes the file, returns `duplicate_of` instead of a copy when the bytes already exist, copies it into the root, probes it and makes a preview. Describe a sound's `--planned-use` by the feeling it gives rather than where one cut placed it, so another project can find it. `LIB archive ID` hides what isn't worth finding again; an asset a past cut used is never deleted.

## 3. Register a bundle when it is about to be reused

When a new project is about to reuse a character, rig, kit, set, material, synthesised sound or helper script from an earlier one, register it from the project where it works (`LIB register --help` has a full example), then copy the snapshot into the new project and record that version when the cut uses it. The profile's reuse rules say what may recur.

What `--help` doesn't tell you:

- Validation runs in a fresh copy of the snapshot, not in the project, with only `PATH`, `HOME`, `LANG`, `TMPDIR` and the names given with `--validate-env`. When it fails, the version is recorded as failed and the command exits 1: add the missing files to `--files` and register again.
- The snapshot keeps file contents, not permission bits. Name the interpreter in the command (`bash check.sh`), or `chmod +x` in `--validate-setup`.
- Validation proves the command exits 0, not that the result looks right. Make it render the example; a command that only parses the source proves nothing.
- The same content gives the same version. Any changed file or setting adds a version, and old versions stay because past cuts point at them.

## 4. Record the cut

Record uses once the cut is delivered, from its final cue sheet or manifest after the last swap; uses recorded mid-project go stale when a track or clip changes. Record what the cut shows or plays and pin what was placed: `file` for media (it is hashed, and a file that isn't the library's copy is refused, so ingest it, as a variant if it was cropped or re-encoded), `artifact_version` for a bundle (from the copied snapshot's `bundle.json`), with `modified` when the project changed it. Detail such as "whoosh" goes in the cue.

`LIB used ID --project … --cut … --role … --file …` records one use. For a whole cut, list the entries in a JSON declaration kept with the project and run `LIB used --from FILE`, which records every entry or none; `check` and `deliver` read the same file:

```json
{"project": "PROJECT", "cut": "v3", "selected": [
  {"id": "sfx-07", "role": "sfx", "file": "audio/sfx-07.flac", "cue": "keyboard", "output_time": 12.4},
  {"id": "walk-rig", "role": "character", "artifact_version": "9c01d5e3aa40", "modified": true}
]}
```

`file` is relative to the declaration's folder, and an empty `selected` list is valid. When a recorded use turns out wrong, record the cut that replaced it and add a `caveat` note to the asset.

Report the video and the catalog status separately; the video ships whatever state the catalog is in.

## 5. Check the record

`LIB check --project P --cut C --declared FILE` checks a cut's record without writing: every declared entry has its use with the right version, and nothing points at a missing file. It also lists unrecorded references, library assets named or byte-matched in the project folder but missing from the declaration; most are rejected candidates, so add one only if the cut really uses it. `LIB deliver` runs the same check and, when it passes, stores the cut's delivery row, listing the bundles registered from the project (`--registered ID@VERSION`, or `--none REASON`).

## Notes

`LIB note ID --kind opinion|test|rights|caveat --text "…" --source "…"` appends a dated note. An opinion is the user's own words with the date and source, never inferred; a judge's or agent's reading is a caveat; a passing validation is a test.

## Without the library

With no library and the user declining one, or with the tool failing, keep the project manifest that the producing skill describes and say the catalog was not updated. Change the database only through commands; `LIB export` writes a full JSON copy.

Before changing `library.py` or the schema, read [records](references/records.md).
