---
name: ugc-video
description: Create UGC-style video ads for TikTok, Reels and Meta: write scripts with a 3-second conflict hook, tear down an uploaded video frame by frame and generate new original scripts, and find and brief creators. Use when the user asks for video scripts, hooks, a video breakdown or 拆解, a creator brief, or influencer/creator outreach. 中文关键词: UGC, 短视频, 视频脚本, 带货视频, 拆解视频, 逐帧拆解, 达人, 红人, KOL.
---

# UGC Video

## Gather context first

Read `.agents/product-context.md` first if it exists and only ask for what is missing. If it doesn't exist, gather product, key benefit, real proof, offer, target viewer and main objection, where goods ship from and real delivery time, and offer to create it (template: `growth-strategy` → `references/product-context-template.md`).

## The 3-second conflict rule (always applies)

The first 3 seconds must contain dramatic conflict: person vs problem, person vs person, expectation vs reality, or stakes against a clock. No conflict means no stop and no retention. Check every hook: if removing the conflict loses nothing, rewrite it.

## What to do

| User wants | Read |
|---|---|
| New video scripts, hooks, creator brief | `references/ugc-video-scripts.md` + `references/conflict-hooks-and-script-example.md` |
| Uploads a video to analyze, break down or remake | `references/ugc-video-teardown.md` + `references/teardown-example.md`, and run `scripts/extract_frames.sh <video> <out_dir>` when a shell with ffmpeg is available |
| Find, vet, contact and pay creators | `references/influencer-outreach.md` + `references/outreach-templates.md` |

## How to work

- If the user seems new or uses an abbreviation you are about to rely on (CPA, ROAS, CAPI, SPF…), explain it in one plain line the first time; definitions: `growth-strategy` → `references/glossary.md`.
- Before answering, read the reference file(s) in the matching row above. Paths are relative to this skill's folder.
- Stay in this skill. Mention related skills as next steps; load another skill only when the user asks for that work or the answer needs its platform-specific details.
- If `.agents/product-context.md` does not exist, end your reply with a one-line offer to save the product facts there.

## Core rules

- Native beats polished: vertical 9:16, real people, real settings, captions on.
- One message per video; write at least five hooks per script.
- Reuse patterns, never content: no copied lines, footage, characters, music or brand names from other videos.
- Never script fake testimonials or medical claims.
- Creators must disclose paid partnerships (FTC; platform labels and #ad).

## Related skills

Run and scale the videos → `paid-ads` · Test and read results → `ads-optimization` · Written copy → `ad-copy`
