---
name: teach-back
description: Find out what the user actually understands about a topic by having them explain it back (the Feynman technique), then probe the gaps one question at a time and end with a one-page cheat sheet and spaced review questions. Works for anything they are studying or have just read, watched or built: a paper, a course, a codebase, an interview topic, a concept. Use when the user says "quiz me", "test my understanding", "help me study", "I'm preparing for an interview on X", "did I get this right", or "make me a cheat sheet".
---

# Teach back

The test of understanding is explaining it simply. If the user can't explain it in plain words, there's a gap, and the gap is the part worth studying. This skill finds the gaps, fills them, and checks again later.

## 1. Set up

Ask one question at a time:
1. What's the topic, and how deep do they need it? ("Enough for a system design interview" is different from "enough to use it at work".)
2. Do they have source material? A paper, notes, a doc, a repo or a video transcript. If they do, read it, and base every question and correction on it, quoting it when you correct.

## 2. They explain, you listen

Ask them to explain the topic as if to a smart friend who's never heard of it. Voice note style is fine. Don't interrupt and don't correct yet.

Then sort what they said into three groups (show this to them briefly):
- **Solid**: correct and in their own words.
- **Fuzzy**: roughly right but vague, hand-wavy, or using jargon they didn't unpack.
- **Missing or wrong**: important parts they skipped, or got wrong.

## 3. Probe the gaps

Work through the fuzzy and missing parts, most important first, **one question at a time**:
- Ask "why" and "what would happen if" questions, not definitions. "What breaks if the cache never expires?" tests more than "What is a TTL?"
- Wait for their answer. If it's right, say so in a few words and move on. If it's wrong or stuck, give the smallest hint that gets them there, not the answer. After two hints, explain it plainly in two or three sentences, then ask them to say it back.
- Use a concrete example with real numbers whenever the topic allows.

Stop after about 8 to 10 questions or when the gaps are closed, whichever comes first. Better to end with energy left.

## 4. Cheat sheet

Write `cheatsheet-<topic>.md`, one page:
- The topic in one sentence.
- The core idea in their words (from step 2, corrected).
- The 5 to 8 things they got wrong or fuzzy, each as one line with the correct version.
- One worked example.
- Words to know, each with a plain one-line meaning.

## 5. Spaced review

Add 5 review questions at the bottom of the cheat sheet, built from their gaps, with answers in a collapsed `<details>` block. Suggest reviewing them tomorrow, in 3 days and in a week, because those spacings are when forgetting is fastest. If the user wants reminders, offer to set them up but don't do it unasked.

## Rules

- They talk more than you do. Your turns are short.
- Never mark something wrong that the source material says is right. When unsure, check the source or say you're unsure.
- No praise inflation. "Right" is enough; save "that's a great explanation" for when it is one.
