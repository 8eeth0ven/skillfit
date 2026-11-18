---
name: ads-optimization
description: Test ad creatives and review paid ads performance across Meta, Google and TikTok: test plans, kill/keep/iterate rules, creative logs, daily checks, weekly reviews, CPA diagnosis and next actions. Use when the user asks how to test creatives, why results dropped, for an ads review or post-mortem (复盘), or how to optimize. 中文关键词: 复盘, 投放复盘, 优化, 素材测试, CPA 上涨, ROAS, 数据分析, 周报.
---

# Ads Optimization

## Gather context first

Read `.agents/product-context.md` first if it exists and only ask for what is missing. If it doesn't exist, gather the facts below and offer to create it (template: `growth-strategy` → `references/product-context-template.md`).

Exported metrics for this period and the previous one (spend, CPM, CTR, CVR, CPA, ROAS, frequency by campaign/ad), store orders for the same period, targets, what changed, and where goods ship from (China direct or local stock).

## What to do

| User wants | Read |
|---|---|
| Plan or read creative tests, kill/keep rules, creative log | `references/creative-testing.md` + `references/creative-log-template.md` |
| Platform-specific fixes (Google search terms, keywords, negatives, PMax; Meta structure and scaling; TikTok setup) | Diagnose here, then load `paid-ads` and read its platform reference before recommending settings |
| Weekly or monthly review, why CPA rose, report | `references/ads-review-optimization.md` + `references/weekly-review-example.md` |

## How to work

- If the user seems new or uses an abbreviation you are about to rely on (CPA, ROAS, CAPI, SPF…), explain it in one plain line the first time; definitions: `growth-strategy` → `references/glossary.md`.
- Take data in whatever form the user has: a screenshot of Ads Manager, a pasted table, or a CSV. Never ask them to export in a special format or connect accounts. Read what they give, check it for consistency, and ask only for the one or two missing numbers that block the diagnosis.
- Before answering, read the reference file(s) in the matching row above. Paths are relative to this skill's folder.
- Stay in this skill. Mention related skills as next steps; load another skill only when the user asks for that work or the answer needs its platform-specific details.
- If `.agents/product-context.md` does not exist, end your reply with a one-line offer to save the product facts there.

## Core rules

- CPA ≈ CPM ÷ (CTR × CVR) ÷ 1000. When CPA moves, find which input moved before acting.
- Test big variables first: concept, then hook, then format, then copy.
- Read metrics top-down: hook rate → hold → CTR → CVR → CPA. Fix the first stage that fails.
- Cross-check platform numbers with real store orders; track MER (revenue ÷ ad spend).
- Change one major thing at a time; end every review with at most three actions.

## Related skills

New creatives → `ad-copy`, `ugc-video` · Account and platform changes → `paid-ads` · Page or offer problems → `growth-strategy`
