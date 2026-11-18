---
name: ad-copy
description: Generate ad copy from many different angles for Meta, Google and TikTok, written in natural native English (default US audience). Use when the user asks for ad copy, hooks, headlines, primary text, RSA headlines, multiple angles or variations, or wants copy that doesn't sound translated. 中文关键词: 广告文案, 文案, 标题, 钩子, 多角度文案, 英文文案.
---

# Multi-Angle Ad Copy

## Goal

A labeled set of ad copy across distinct angles and platforms, ready to test, that sounds like it was written by a native speaker.

## Before you start: gather context

Read `.agents/product-context.md` first if it exists and only ask for what is missing. If it doesn't exist, gather the facts below and offer to create it (template: `growth-strategy` → `references/product-context-template.md`).

- Product, price, offer, key benefits and proof (reviews, numbers, guarantees)
- Target customer and their main problem
- Awareness level of the audience (see below)
- Platforms and placements
- Words or claims to avoid (compliance, brand voice)
- Where goods ship from (China direct or local stock) and the real delivery time; ask if unknown

## Awareness levels

Match the opening to how much the reader already knows:

1. **Unaware**: lead with a story, a surprising fact or a relatable moment
2. **Problem-aware**: name the problem in their words
3. **Solution-aware**: show why this approach beats the alternatives
4. **Product-aware**: proof, comparison, offer
5. **Most aware**: offer and urgency only

## Angle library

Generate at least one variant per relevant angle:

| Angle | Core idea |
|---|---|
| Pain | The frustration they feel today |
| Outcome | The life after the problem is solved |
| Social proof | What other customers say or how many use it |
| Authority | Expert, certification, press, data |
| Comparison | Us vs the usual option (without naming competitors unfairly) |
| Objection buster | Answer the main reason people hesitate |
| Demo / how it works | Show the mechanism in one line |
| Story | Founder or customer story |
| Identity | Who this product is for ("for people who…") |
| Value | Cost per use, savings, bundle |
| Risk reversal | Guarantee, free returns, trial |
| Curiosity | An unexpected claim that makes them stop |
| Honest urgency | Real deadlines or limited stock only |

Copy frameworks to structure longer text: PAS (problem, agitate, solution), BAB (before, after, bridge), AIDA.

## Platform formats

- **Meta**: primary text (first ~125 characters show before "See more", so put the hook there), headline (~40 characters), description optional, CTA button
- **Google RSA**: headlines up to 30 characters, descriptions up to 90 characters; each headline must work alone in any combination
- **TikTok**: short ad text (keep it brief), with the real hook in the video's first seconds and on-screen text

## Writing native-sounding English

- Conversational, second person, short sentences, contractions ("you'll", "it's")
- Specific beats generic: "dries in 10 minutes" beats "fast-drying"
- Avoid patterns that read as translated: "high quality", "best choice", "Dear customer", "Our company is professional", stacked adjectives, random capitalization, exclamation marks everywhere
- Avoid policy risks: no personal-attribute questions, no unprovable superlatives (see `paid-ads` (`references/ad-policy-compliance.md`))

## Workflow

1. Confirm product facts and proof; never invent numbers, reviews or claims.
2. Pick the 5–8 most relevant angles for the awareness level.
3. For each angle, write 3 hooks, then full copy for the best one per platform.
4. Label every variant so test results can be traced back to the angle.
5. Flag any claim the user must verify.

## Output format

Table: ID, angle, awareness level, platform, hook, primary text / description, headline, CTA, claims to verify. Then a short note on which 3 variants to test first and why.

## How to work

- If the user seems new or uses an abbreviation you are about to rely on (CPA, ROAS, CAPI, SPF…), explain it in one plain line the first time; definitions: `growth-strategy` → `references/glossary.md`.
- Before answering, read the reference file listed under References below. Paths are relative to this skill's folder.
- Stay in this skill. Mention related skills as next steps; load another skill only when the user asks for that work or the answer needs its platform-specific details.
- If `.agents/product-context.md` does not exist, end your reply with a one-line offer to save the product facts there.

## References

- `references/hook-bank-and-native-english.md`: hook templates by angle, worked example, translated-to-native fixes

Related skills: video scripts → `ugc-video` · testing copy → `ads-optimization` · platform setup → `paid-ads`
