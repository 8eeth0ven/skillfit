---
name: paid-ads
description: Set up, launch, scale and troubleshoot paid ads on Meta (Facebook/Instagram), Google (Search, Shopping, PMax) and TikTok for overseas markets (default US), including conversion tracking and ad policy compliance. Use when the user asks about any ad platform, campaign structure, budgets, scaling, optimizing a Google account (search terms, keywords, negatives, PMax, bidding), Meta or TikTok settings, Pixel/CAPI/GA4/UTMs, rejected ads or account bans. 中文关键词: 开户, 代理开户, 小预算, 黑五, 网一, 旺季, 圣诞, 商品目录, 动态广告, 再营销, 投放, 广告投放, Meta 广告, Facebook 广告, Google 广告, 谷歌广告, TikTok 广告, 搜索词, 否定词, 放量, 像素, 封号, 拒审.
---

# Paid Ads

## Gather context first

Read `.agents/product-context.md` first if it exists and only ask for what is missing. If it doesn't exist, gather the facts below and offer to create it (template: `growth-strategy` → `references/product-context-template.md`).

Platform(s), product, price, gross margin, target CPA or ROAS, budget, tracking status, account history, and current numbers (last 7 and 30 days) if live. Where goods ship from (China direct or local stock) and the real delivery time; ask if unknown, since it changes what you can promise.

## What to do

| User wants | Read |
|---|---|
| Open or set up ad accounts (Meta, Google, TikTok): self-serve vs official agency, documents, verification, permissions | `references/account-setup.md` |
| Small budget (about $500–2,000): whether to run ads, a two-week plan, decision rules | `references/small-budget-start.md` |
| Black Friday, Cyber Monday, Q4, Christmas, peak-season budgets, offers and timelines | `references/peak-season-bfcm.md` + `growth-strategy` → `references/global-holidays.md` |
| Product catalogs, dynamic / Advantage+ catalog ads, retargeting, audience exclusions | `references/catalog-and-retargeting.md` |
| Meta ads: structure, testing, kill/keep, scaling, new-account ramp, troubleshooting | `references/meta-ads.md` + `references/launch-checklist.md` |
| Google ads: campaign mix, keywords, negatives, RSAs, feeds, bidding | `references/google-ads.md` + `references/keywords-and-rsa-example.md` |
| TikTok ads: creative-first setup, Spark Ads, refresh cadence | `references/tiktok-ads.md` + `references/creative-calendar.md` |
| Pixel, Conversions API, Events API, enhanced conversions, GA4, UTMs | `references/tracking-setup.md` + `references/qa-checklist.md` |
| Rejected ads, restrictions, bans, pre-launch compliance check | `references/ad-policy-compliance.md` + `references/risky-phrases.md` |

## How to work

- If the user seems new or uses an abbreviation you are about to rely on (CPA, ROAS, CAPI, SPF…), explain it in one plain line the first time; definitions: `growth-strategy` → `references/glossary.md`.
- Take data in whatever form the user has: a screenshot of Ads Manager, a pasted table, or a CSV. Never ask them to export in a special format or connect accounts. Read what they give, check it for consistency, and ask only for the one or two missing numbers that block the diagnosis.
- Before answering, read the reference file(s) in the matching row above. Paths are relative to this skill's folder.
- Stay in this skill. Mention related skills as next steps; load another skill only when the user asks for that work or the answer needs its platform-specific details.
- If `.agents/product-context.md` does not exist, end your reply with a one-line offer to save the product facts there.

## Core rules

- No spend before tracking passes QA.
- Start broad with strong creative; keep structures simple so each ad set gets enough data.
- Judge on rules, not one day of data: give ads about 1–2× target CPA before cutting unless early metrics are clearly poor.
- Scale winners gradually (about 20% every 2–3 days); go horizontal when CPA starts rising.
- Comply, never evade: no cloaking, no bought or rented accounts, no new accounts to dodge bans.
- Platform features change; confirm current options in each ads manager.

## Related skills

Network, IP checks and login problems → `network-environment` · Copy → `ad-copy` · Video creatives → `ugc-video` · Weekly review and creative testing → `ads-optimization` · Landing page and offer → `growth-strategy`
