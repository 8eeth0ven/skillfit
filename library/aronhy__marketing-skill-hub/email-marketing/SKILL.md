---
name: email-marketing
description: Plan and write automated email flows and campaigns for opted-in subscribers and customers in overseas markets (default US): welcome, abandoned cart, browse abandonment, post-purchase, review requests, win-back, and a holiday campaign calendar. Use when the user asks about email marketing, Klaviyo or Shopify Email flows, abandoned cart emails, retention, or repeat purchases. 中文关键词: 邮件营销, 欢迎邮件, 弃单邮件, 弃购, 召回邮件, 物流通知, Klaviyo.
---

# Email Lifecycle Marketing

## Goal

Automated flows that turn paid traffic into repeat revenue, plus a campaign calendar built around overseas shopping seasons.

## Before you start: gather context

Read `.agents/product-context.md` first if it exists and only ask for what is missing. If it doesn't exist, gather the facts below and offer to create it (template: `growth-strategy` → `references/product-context-template.md`).

- Store platform and email tool
- List size, how subscribers are collected, current flows
- Product type and typical repurchase cycle
- Brand voice and offers the user is willing to give
- Where goods ship from (China direct or local stock) and the real delivery time; ask if unknown

## Core flows

| Flow | Trigger | Emails | Purpose |
|---|---|---|---|
| Welcome | Signs up | 3–5 over ~10 days | Brand story, best sellers, first-order offer, social proof |
| Abandoned checkout | Starts checkout, no purchase | 2–3 over ~3 days | Reminder, answer objections, optional incentive last |
| Abandoned cart / browse | Adds to cart or views product | 1–3 | Bring them back to the product |
| Post-purchase | Orders | 3–4 | Thank you, shipping expectations, how to use, review request, cross-sell |
| Review request | Product delivered + time to use | 1–2 | Collect real reviews and photos |
| Replenishment | Expected run-out date | 1–2 | Reorder reminder for consumables |
| Win-back | No purchase in X days | 2–3 | Remind, new arrivals, offer |
| Sunset | No opens or clicks for a long period | 1–2 | Re-confirm interest, then suppress to protect deliverability |

Build in this order: welcome, abandoned checkout, post-purchase, then the rest.

## Campaign calendar (US default)

Valentine's Day, Mother's Day, Memorial Day, Father's Day, Fourth of July, back to school, Labor Day, Halloween, Black Friday and Cyber Monday, holiday season and last shipping day before Christmas, New Year. Plan BFCM offers and creatives by October. Adjust for other markets' holidays.

## Writing rules

- One goal per email, one primary CTA
- Subject lines that are clear and honest; preview text that adds information
- Mobile-friendly design, short paragraphs, real product photos
- Plain-text style emails often perform well for founder notes and win-back
- Never fake urgency or fake reviews

## Consent and compliance

- Email only people who opted in (customers and subscribers); do not import scraped lists into the marketing tool.
- Include unsubscribe links and a physical address; honor opt-outs (CAN-SPAM in the US; stricter consent rules in the EU, UK and Canada).
- SMS marketing has separate, stricter consent requirements; treat it separately.

## Metrics

Revenue per recipient, click rate, conversion rate, unsubscribe and spam complaint rates, flow revenue share of total. Open rates are less reliable because of privacy features in mail apps.

## Output format

1. Flow map table with triggers, timing and goals
2. Full copy for each email in the requested flows: subject, preview text, body, CTA
3. A 12-month campaign calendar with suggested themes
4. KPIs to track

## How to work

- If the user seems new or uses an abbreviation you are about to rely on (CPA, ROAS, CAPI, SPF…), explain it in one plain line the first time; definitions: `growth-strategy` → `references/glossary.md`.
- Before answering, read the reference file listed under References below. Paths are relative to this skill's folder.
- Stay in this skill. Mention related skills as next steps; load another skill only when the user asks for that work or the answer needs its platform-specific details.
- If `.agents/product-context.md` does not exist, end your reply with a one-line offer to save the product facts there.

## References

- `growth-strategy` → `references/global-holidays.md`: holidays and shopping festivals by market for the campaign calendar

- `references/flow-copy-examples.md`: welcome, abandoned checkout and post-purchase copy, win-back, 12-month calendar

Related skills: cold prospecting (non-subscribers) → `cold-outreach` · offers and proof → `growth-strategy`
