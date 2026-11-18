---
name: growth-strategy
description: Start here for overseas marketing (default market: US). Builds a 90-day growth plan, researches market demand and competitors' ads, sharpens positioning and offers, and plans landing pages. Use when the user asks where to start, wants a marketing or go-to-market plan, market research, competitor ad research, pricing or offer help, or a landing page. 中文关键词: 节假日, 节日, 大促, 营销日历, 欧洲, 东南亚, 拉美, 俄罗斯, 加拿大, 进入新市场, 术语, 什么意思, 新手, 常见问题, 独立站还是亚马逊, 美国公司, 销售税, 关税, 商标, 认证, 封号, 封店, 起步资金, 出海, 海外营销, 增长计划, 市场调研, 竞品广告, 定位, 报价, 落地页, 发货方式, 中国直发, 海外仓, FBA.
---

# Growth Strategy

Entry point of this library. Decide what the user needs, read only the matching reference, and route to other skills when the work moves on.

## Gather context first

Read `.agents/product-context.md` first if it exists and only ask for what is missing. If it doesn't exist, gather the facts below and offer to create it (template: `references/product-context-template.md`).

Product, price, gross margin, B2C or B2B, target market (default US), **where goods ship from** (China direct, or local stock: US warehouse / 3PL / FBA; always ask if unknown, because it changes the whole plan), monthly budget, current stage (idea / first sales / scaling), assets in place (site, pixel, reviews, creatives, email list).

## What to do

| User wants | Read |
|---|---|
| Beginner questions (100 FAQ): product choice, Amazon vs own website, US company, payments, US sales tax and income tax, tariffs, trademarks, certifications, account or store bans, website basics, ads, creatives, creators, logistics, returns, customer service, scams, startup budget, how long to profit | `references/beginner-faq.md` |
| What a term or abbreviation means (CPA, ROAS, CPM, CAPI, PMax, SPF…), beginner explanations | `references/glossary.md` |
| Holidays and shopping festivals by market (US, Canada, Europe, Southeast Asia, Latin America, Russia), yearly campaign calendar | `references/global-holidays.md` |
| Entering a market: language, platforms, payments, tax, compliance, sanctions (US, Canada, Europe, SEA, LatAm, Russia) | `references/market-notes.md` |
| Set up the shared product context used by every skill | `references/product-context-template.md` |
| Where goods ship from, China direct vs US warehouse / FBA / FBM, delivery promises | `references/fulfillment.md` |
| Where to start, 90-day plan, which channel, budget split | `references/growth-plan.md` + `references/90-day-plan-example.md` |
| Can this sell overseas, demand, unit economics | `references/market-research.md` + `references/unit-economics.md` |
| What competitors run, swipe file, gaps | `references/competitor-ad-research.md` + `references/swipe-file-template.md` |
| Positioning, offers, objections, "clicks but no sales" | `references/offer-positioning.md` + `references/positioning-example.md` |
| Landing page outline, copy, CRO review | `references/landing-page.md` + `references/page-copy-example.md` |

## How to work

- If the user seems new or uses an abbreviation you are about to rely on (CPA, ROAS, CAPI, SPF…), explain it in one plain line the first time; definitions: `references/glossary.md`.
- Before answering, read the reference file(s) in the matching row above. Paths are relative to this skill's folder.
- Stay in this skill. Mention related skills as next steps; load another skill only when the user asks for that work or the answer needs its platform-specific details.
- If `.agents/product-context.md` does not exist, end your reply with a one-line offer to save the product facts there.

## Core rules

- Fix foundations before spending: tracking, a trustworthy page, a clear offer.
- One primary paid channel until it is profitable.
- Break-even ROAS = 1 ÷ gross margin. Know it before launching ads.
- Evidence over opinion: every demand claim needs a source.
- Never invent reviews, numbers or fake scarcity.
- Where goods ship from decides delivery promises, costs and messaging. Follow the matching path in `references/fulfillment.md`.

## Route to other skills

| Next step | Skill |
|---|---|
| Launch and manage Meta, Google or TikTok ads; tracking; policy | `paid-ads` |
| Write ad copy | `ad-copy` |
| Video scripts, video teardown, creators | `ugc-video` |
| Test creatives, weekly review, diagnose CPA | `ads-optimization` |
| B2B prospecting, 开发信 | `cold-outreach` |
| Email flows for subscribers and customers | `email-marketing` |
| 私域: lead registration, screening, chat scripts, FAQ | `conversational-sales` |
| Network and IP checks, which network to use for accounts, login challenges, account association | `network-environment` |
| Organic social: TikTok, Instagram, YouTube, Pinterest and others; what and how often to post | `social-media` |
