---
name: brand-kit
description: Learn a company's brand design from its live website (colours, fonts with the real font files, logo, button and card shapes, texture, image style) and save it as a reusable kit that vox-explainer and image-gen apply automatically. Use FIRST, before any brand or sponsored video, sticker, graphic or asset for a company (e.g. "a video for Devin", "ChatGPT-style stickers", "match their brand"), or when asked to get, learn, extract or match a brand's look.
---

# Brand kit

**Run this before making anything for a brand.** vox-explainer refuses a `"brand"` scene with no kit, and image-gen refuses `--brand` with no kit.

Kits live in `~/.local/share/simcraft/brands/<slug>/`, outside the public repo, because they hold other companies' fonts and logos. Use them only for work with or about that brand, and never commit or share the font files.

## Steps

1. **Extract.** Give the main site, plus the product or marketing page if it looks different. The second page often holds the real brand font (chatgpt.com uses system fonts, openai.com ships OpenAI Sans).
   ```
   node ~/simcraft/skills/design/brand-kit/scripts/extract.mjs https://devin.ai ~/.local/share/simcraft/brands/devin [more urls]
   ```
   It reads the CSS design tokens (resolving nested ones), the computed styles of headings, body, buttons, code and cards, the `@font-face` files (downloaded locally), the logo, the favicon, and the colours that cover the screen by area.
2. **Propose:** `python3 ~/simcraft/skills/design/brand-kit/scripts/propose.py <brand_dir> --name "Devin"` writes `brand.json`.
3. **Board:** `python3 ~/simcraft/skills/design/brand-kit/scripts/board.py <brand_dir>` writes `board.png`. It shows the palette, the real fonts, the logo, the site, and two sample explainer frames in the brand's look. **Look at it** next to the site screenshot and fix `brand.json` by hand where it's off:
   - **accent:** the one colour the brand is known for. If the brand is monochrome (like ChatGPT), the accent is black, and that's correct.
   - **vox.field_a / field_b:** the two background fields. Usually the brand's surface plus either its ink or its accent.
   - **fonts.display:** the face, weight and case of their headlines.
   - **image_style:** one sentence describing how their illustrations look. Write it from their site, not from the template.
   - Note anything else in `notes`, such as "never use the logo on blue" or "emoji-free".
   Then re-run the board, and show it to the user before using the kit.
4. **Check official guidelines** if the brand publishes them (search "<brand> brand guidelines" or "press kit"). Official colours and logo files beat what the website happens to use.

## Using a kit

- **vox-explainer:** add `"brand": "devin"` to the scene. Colours, fonts, edges (clean or torn), grain and highlight all switch over. Background names become `a`, `b`, `paper` and `accent`.
- **image-gen:** add `--brand devin`. The kit's image style and palette are added to every prompt.
- For anything else (stickers, thumbnails, slides), read `brand.json` and use its colours, font files and shapes.

## What the kit holds

`colors` (surface, paper, ink, muted, accent, on_accent, extras), `fonts` (display, body, mono, and serif if any, each with its family, weight, case, tracking and local files), `shape` (button and card radius, texture), `logo`, `icon`, `vox` (the explainer theme), `image_style` and `notes`.

How each choice is made, and what testing on Devin and ChatGPT showed: [reference.md](reference.md).
