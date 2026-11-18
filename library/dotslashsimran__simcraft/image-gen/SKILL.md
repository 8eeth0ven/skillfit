---
name: image-gen
description: Generate images with the user's own API keys (Google Gemini "Nano Banana" or OpenAI gpt-image). Use when asked to generate, create or make an image, illustration, icon, cut-out, sticker, thumbnail, texture, mockup or visual asset, to edit an image, or to make several images that stay consistent (same character or object). Also used by the vox-explainer skill for collage cut-outs.
---

# Image gen

```
python3 ~/simcraft/skills/design/image-gen/scripts/gen_image.py "<prompt>" --out <dir> --name <name> [options]
```
Standard library only, so any `python3` works.

## Keys

The script reads `GEMINI_API_KEY` and `OPENAI_API_KEY` from the environment, or from `~/.config/simcraft/keys.env` (one `NAME=value` per line, chmod 600).
- Run `--check` to see which keys are set. It never prints a key.
- If no key is set, tell the user to open the file themselves (`open -e ~/.config/simcraft/keys.env`) and paste it in. Never ask them to paste a key into chat, and never read keys out of other projects' files.
- Keys go only in request headers. They never go in a URL, a log, or a sidecar file.
- Get a Gemini key at aistudio.google.com/apikey (it has a free tier). Get an OpenAI key at platform.openai.com/api-keys.

## Options

| Option | What it does |
|---|---|
| `--n 4` | Makes 4 variations in parallel, plus `<name>_sheet.png` to pick from. Use this for anything that matters. |
| `--aspect 16:9` | Sets the shape: 16:9, 9:16, 1:1, 4:3 or 3:4. Match it to where the image goes. |
| `--ref a.png b.png` | Reference images. Use them to edit an image, match a style, or keep the same character or object across images. |
| `--cutout` | Gives a transparent PNG for collages. Gemini generates on chroma green and the script keys it out with clean edges. OpenAI makes real transparency. |
| `--provider gemini\|openai` | Picks the provider. Default: Gemini if its key is set. |
| `--model M` | Picks the model. By default Gemini picks the newest image model the key can use (`--models` lists them), and OpenAI uses gpt-image-2. |
| `--quality low\|medium\|high` | OpenAI only. Default high. |
| `--brand devin` | Adds a brand kit's image style and palette to the prompt. **For any brand work, run the brand-kit skill first.** |

Every image gets a `<name>.json` sidecar with the exact prompt, model and settings, so it can be remade or tweaked later.

## Which provider

- **Gemini:** fast and cheap. Best for iterating, for edits, and for keeping things consistent with `--ref`.
- **OpenAI gpt-image:** best for images with text in them, and for true transparent cut-outs.

## Prompting

- Describe the subject, the medium, the light and the framing, in that order. Say what to leave out.
- **No text in images** unless the user asks for it. Models still misspell words. Add type afterwards in code.
- For a series, generate one anchor image first. Then pass that same anchor as `--ref` to every other image. Never chain image 2 into image 3, because small errors pile up.
- Show the user the contact sheet before using images anywhere. Regenerate one variation instead of all of them.
