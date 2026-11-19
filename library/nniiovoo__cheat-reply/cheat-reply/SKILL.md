---
name: cheat-reply
description: Find promising X/Twitter conversations, study their replies, and draft distinctive replies people have a reason to answer or share. Use for reply discovery, comment research, reply drafting, or reply growth strategy. Adapt to the user's audience, language, and voice; posting requires approval of the exact text and target.
license: MIT
metadata:
  version: "0.2.1"
  maintainer: nniiovoo
---

# Cheat Reply

Learn what earns attention in a conversation before joining it. Aim for a reply that gives the user's intended audience a reason to notice, answer, or share it. A smaller relevant conversation can be worth more than unrelated viral exposure.

For growth requests, optimize both the opportunity and the draft. The user's purpose still comes first: a helpful answer, a professional relationship, or a sincere thank-you should not be turned into a joke or provocation to chase reach.

This skill is for replies and conversation research, rather than original posts or engagement predictions.

## Choose the mode

- **Learn:** study posts and comments; record useful observations without drafting or posting.
- **Draft:** research the conversation and propose a reply. This is the default.
- **Post an approved reply:** publish only the exact text to the exact target the user has approved, then verify the result. A learning or drafting request does not authorize posting.

Use the user's topic, target, audience, language, tone, and constraints when supplied. Otherwise infer what is clear from the request and ask only for missing information that affects the work. Let the user's context set the defaults.

## Load only useful context

If present in the user's working project:

1. Read the current rules and latest five cases in `reply-learnings.md`.
2. Read only the voice and audience sections of `audience.md` when needed.

These files are optional. Without them, use the user's stated voice and audience; do not invent a persona or performance history. Blank starting points are in [examples](examples/). Keep the user's real notes in their project, outside this installed skill.

Read [the playbook](references/reply-playbook.md) for strategy, repeated underperformance, or skill maintenance. Read [research and limitations](references/research-basis.md) when explaining ranking or evidence behind the workflow. Ordinary single-reply work does not need either full reference.

## Find worthwhile conversations

For discovery, weigh:

- **Audience fit:** would the people reading this care about the user's work or interests?
- **Activity and timing:** look for continuing conversation or attention from the intended audience. A fresh post can have few views because it is still early. Infer momentum only from multiple observations or another visible activity signal, not a single snapshot.
- **Room to contribute:** check the replies for a useful angle that is still missing. A crowded viral thread full of the same joke can be a worse opportunity than a smaller, active discussion.
- **Natural response:** can the author or other readers meaningfully answer or extend the reply? Their participation is useful; never promise it or assume it exposes the reply to all their followers.
- **Context:** read the complete post, expand hidden text, and inspect relevant media before committing to an angle.

Use specific topics, accounts, or phrases from the user's interests rather than a broad search that mixes unrelated audiences. Examples across different topics include `sourdough starter`, `marathon training`, and `design systems`. Choose terms that fit the actual request. If X search filters fail, simplify the query.

Set reach and timing criteria for the user's audience and goals, rather than applying fixed view, like, or reply-count thresholds. The user's supplied target takes precedence over a discovery heuristic.

For discovery, compare the available targets and explain the strongest opportunity briefly. Prefer audience fit, observed activity, and a distinct contribution over the biggest raw view count. Being early creates an opportunity to join; it does not guarantee placement in ranked replies.

Track targets already replied to during the current session. In discovery, skip those posts and avoid repeatedly selecting the same account within a batch. User-requested follow-ups, revisions, and continuing an existing conversation are different from finding a new target; do not block them as duplicates.

## Learn before writing

For the target, inspect relevant or top replies and note what receives attention:

- Is the useful contribution a punchline, concrete question, counterexample, explanation, or personal experience?
- Does it agree, challenge, extend, or clarify the original post?
- What makes it specific to this conversation?

Identify the mechanism behind a strong reply: useful new information, recognition, surprise, humor, a clear explanation, or an answerable question. Compare with an ordinary or repetitive reply when available. Note visible engagement, reply age, and account/relationship advantages when known; a famous author's comment is not proof its wording caused the result.

Find the gap: what is the original post inviting, what have replies already said, and what useful or entertaining contribution is missing? Do not reproduce the leading joke or rephrase a top comment as if it were a new idea.

When the target's replies are too fresh, sparse, repetitive, or otherwise weak as evidence, study a discussion on the same topic with clearer meaningful engagement relative to that audience. An active thread of interchangeable praise is not sufficient evidence of an effective reply pattern. Look for substantive responses or a useful contrast among comments, without requiring a fixed like count or a large account. If a stronger comparison is unavailable, state the evidence limit rather than inventing a winning pattern. Reuse a pattern across a closely related batch only when the context still fits. Learn the mechanism; do not copy another person's wording.

Use available browsing or approved computer-use tools. If comments are inaccessible, ask the user to paste the post and a few relevant replies. State what you could inspect; do not invent comment evidence, engagement counts, or a winning pattern.

## Develop and choose the draft

For a growth-oriented draft, privately explore a few genuinely different angles before choosing one. Options might include a useful reframe, concrete observation, recognition or humor, a well-supported challenge, or a precise question. Do not make superficial rewrites of the same line. Use only angles that fit the user's voice and the evidence.

Compare the candidates with plain agreement or praise. The selected reply should give someone a reason to interact with this reply, rather than merely agree with the original post. Present one strongest candidate; offer alternatives when the direction genuinely branches or the user asks.

- Make one point, using a concrete detail from the post.
- Match the user's voice and the conversation. Short and dry can work; thoughtful technical discussions may need an explanation or a precise question.
- For substantive posts, add something that shows you read the material. Generic praise and a forced joke add little.
- Use the author's wording only when it supports a natural extension or reversal.
- Keep slang, emoji, and links purposeful. Avoid repetitive emoji, padded caveats, stock aphorisms, forced contrasts, and a formulaic three-part conclusion.
- Never fabricate the user's experience, qualifications, results, conversations, or insider access. Ask for a real detail when it is essential.

Before presenting it, check:

- **Added value:** what does this contribute beyond the post and the replies already visible?
- **Reaction:** why would the intended reader answer, save, share, or remember it? Name a plausible reason, not a predicted count.
- **Clarity:** is the point understandable on the first read, with a concrete detail instead of a vague slogan?
- **Distinctness:** could the same sentence be pasted under many unrelated posts? If so, make it specific or discard it.
- **Shareability or conversation:** where natural, does an idea or phrase still work when quoted elsewhere, or does a specific question give the author a useful opening? Do not force every technical question to be a standalone punchline.

Revise a weak candidate before showing it. If the context offers no worthwhile contribution, say so instead of filling the thread with generic praise or manufactured disagreement. Do not invent certainty, personal experiences, outrage, or engagement bait to make a line stronger.

Keep drafts concise. Before posting, check the current composer's limit; do not assume every account or format has the same limit. Without composer access, do not claim that you verified the platform's current limit.

Identify the target link/account when available. Briefly combine the observed comment pattern, why this conversation is worth joining, and the chosen reply's reason for earning attention; then show the reply. Keep these notes compact and outside the copyable text unless the user asks for a full audit. Mention limitations that affect the decision, rather than appending generic reach disclaimers to every draft. Do not invent a virality score, probability, or expected reach. For pasted material without a link, identify the supplied post; a missing URL does not prevent drafting. Separate observations from your interpretation.

## Record useful learning

When learning is requested or a reusable observation emerges, add a compact entry to the user's project notes:

```markdown
| Date | Topic/target | Observed reply pattern | Evidence/limitation | Observed result, if available | Lesson to test |
|---|---|---|---|---|---|
```

Save a short paraphrase and a source link where useful. Do not archive private messages or long copied comments. Periodically merge repeated cases into the current rules. Keep observations distinct from proven causes of engagement; this workflow does not predict results.

When the user asks to evaluate results, compare replies at similar observation ages and in comparable conversations. Separate views from likes, meaningful responses, reposts, and any available profile visits or follows. Record timing, target activity, and limitations rather than crediting the wording alone. Keep useful patterns, record counterexamples, and avoid treating one successful reply as a universal formula.

## Publish only approved text

Use an available, authorized posting tool or a browser already signed into the intended account.

1. Confirm the signed-in account, exact target, and approved text.
2. Open the reply composer and check its target and focus before typing.
3. Inspect the complete text in the composer before sending.
4. Send once, then verify the posted reply or a reliable sent confirmation.

If navigation, focus, text, or account is wrong, stop and correct it before sending. If a send may have succeeded, check for the posted reply before retrying to avoid duplicates. If the interface remains unreliable, provide the target link and approved text for manual posting.

Do not post unsupported allegations, fake insider claims, or undisclosed promotions. Do not turn research into unsolicited mass replies or manufactured engagement.
