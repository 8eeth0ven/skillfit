---
name: network-environment
description: Diagnose whether a seller's network and account setup is safe for running ad accounts, store back offices (Shopify, Amazon), social accounts and cold email. Reads an IP check result (for example a ping123.app screenshot), asks how the network is used, rates each scenario as suitable, risky or unsuitable, and gives fixes. Also explains IP types and how platforms judge logins, and handles login challenges, locked accounts and blacklisted IPs. Use when the user asks about IPs, residential vs datacenter IPs, VPN or proxy nodes, which network to use for accounts, IP checks, verification prompts, account association or blacklisting. 中文关键词: IP, 住宅 IP, 机房 IP, 机场, 节点, 网络环境, IP 检测, ping123, 账号关联, 登录验证, 风控, 黑名单, 账号安全.
---

# Network Environment (网络环境检测)

## Gather context first

Read `.agents/product-context.md` first if it exists and only ask for what is missing. If it doesn't exist, gather the facts below and offer to create it (template: `growth-strategy` → `references/product-context-template.md`).

Ask for an IP check result: a screenshot or text from ping123.app (https://ping123.app/) run on the network in question; for cold email, the sending IP and domain instead. Then ask the setup questions in `references/diagnosis-rubric.md` (step 2): what the network is used for, how it was obtained, how often the IP changes, how many people and accounts share it, usual login location, recent incidents, 2FA.

## What to do

| User wants | Read |
|---|---|
| Check whether a network is OK for ads, store, social or email; sends a ping123 or other IP check | `references/diagnosis-rubric.md`, then `references/scenarios.md` for the scenarios involved |
| Understand IP types, residential vs datacenter vs mobile vs shared VPN nodes, how platforms judge IPs | `references/ip-basics.md` |
| What network and account setup each scenario needs (ads, Shopify, Amazon, social, email, website) | `references/scenarios.md` |
| Login challenge, locked account, restricted ad account, blacklisted IP or domain | `references/incidents.md` |

## How to work

1. Read the check result into the five fields in `references/diagnosis-rubric.md` (type, ASN, location, proxy flag, blacklist). Mark unreadable fields 未知; never guess.
2. Ask only the setup questions that would change a verdict.
3. Rate every scenario the user cares about with the rubric: suitable / risky / unsuitable, with the rule that triggered it.
4. Output the report template from the rubric: one-line verdict first, then the scenario table, at most three actions for now, longer-term advice, and missing info.
5. If there is an active incident, add the matching steps from `references/incidents.md`.
- If the user seems new or uses an abbreviation, explain it in one plain line the first time; definitions: `growth-strategy` → `references/glossary.md`.
- Stay in this skill. Mention related skills as next steps (`paid-ads`, `social-media`, `cold-outreach`).
- If `.agents/product-context.md` does not exist, end your reply with a one-line offer to save the facts there.

## Core rules

- Stable and consistent beats "looks local": fixed network, few accounts per environment, consistent business details and payment methods.
- Shared VPN nodes are unsuitable for business accounts: many users, abuse history, constant switching.
- One person, one login; team access through official tools (Meta Business Suite, TikTok Business Center, Shopify staff accounts, YouTube channel permissions); 2FA for every admin.
- For Amazon, treat shared devices, networks, payments or addresses across stores as association risk; multiple stores need legitimate separate entities and Amazon's approval where required.
- Cold email is judged on the sending IP and domain, not the office network.
- In mainland China, cross-border connectivity should go through channels approved by telecom regulators (for businesses, licensed carriers' cross-border services); unauthorized VPN services carry legal risk. Tell the user to confirm current rules.
- Out of scope: rating or improving setups meant to disguise location to bypass a platform's regional restrictions, fingerprint spoofing, anti-detect multi-accounting, buying or renting accounts, evading bans. Say briefly that these break platform rules and put accounts and funds at risk, then give the compliant route.
- Do not invent check results, platform thresholds or policies; platform rules change, so tell the user to confirm them.

## Related skills

Ad account setup and policy → `paid-ads` · Social account operations → `social-media` · Sending domains and deliverability → `cold-outreach` · Beginner questions → `growth-strategy` → `references/beginner-faq.md`
