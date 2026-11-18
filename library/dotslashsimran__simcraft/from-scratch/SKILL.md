---
name: from-scratch
description: Learn how something really works by building the smallest working version of it from scratch, Karpathy style, one small step at a time, with the user predicting what each step will do before running it. Works for ML and AI ideas (attention, tokenizers, backprop, RAG, agents), systems (a database, an HTTP server, git, a shell) and anything else that can be coded. Use when the user says "teach me how X works", "build X from scratch", "I want to really understand X", "explain X from first principles", or "implement X without the library".
---

# From scratch

Reading about a thing gives you the words. Building it gives you the understanding. The fastest way to really get attention, a tokenizer, a vector database or git is to write the smallest version that works, in plain code, and watch it run.

The goal is understanding, not a finished library. Small and readable beats complete.

## 1. Find the core

Ask one question first: what does the user already know? (For example: "Comfortable with Python and numpy? Seen matrix multiplication before?") Then name, in one or two sentences, **the one mechanism that makes the thing work**. Examples:
- Attention: every token scores every other token, and takes a weighted average of their values.
- Git: files are stored by the hash of their contents, and a commit is a file that points at a tree and a parent.
- RAG: turn text into vectors, find the nearest ones to the question, paste them into the prompt.

Everything that isn't the core (speed, edge cases, config, error handling) is left out on purpose. Say what's left out and why.

## 2. Plan the build

Break it into 4 to 8 steps. Each step adds one idea and ends with something that runs and prints a result. Target the whole thing at **under 200 lines**, one file, standard library or numpy only unless the idea needs more. Show the step list, then start step 1.

## 3. Each step

1. **Say the idea** in two or three plain sentences.
2. **Ask for a prediction** before running anything: "What do you think this prints?" or "Which word will get the highest score?" Wrong guesses are where the learning happens, so wait for one.
3. **Write the code** for that step only. Short functions, honest variable names, a comment only where the why isn't obvious.
4. **Run it** and show the real output. Use tiny inputs (3 tokens, 2 files, a 4-word vocabulary) so every number can be checked by eye.
5. **Compare with the prediction.** If it was wrong, explain what they missed, in one or two sentences.

Never write two steps at once. The user can say "faster" to combine steps.

## 4. Check against the real thing

When the toy works, run the same input through the real library or tool (PyTorch attention, real git, a real tokenizer) and show that the answers match, or explain exactly why they differ. This is what turns "I made a toy" into "I know how it works".

## 5. Lock it in

End with:
- A **one-paragraph explanation in the user's words**: ask them to explain it back first, then tidy what they wrote rather than replacing it.
- **Three questions** that test the core idea, answers hidden until they try. (The `teach-back` skill can take it from here.)
- **Where the real version is more complicated**, as a short list, so they know what they skipped.

Keep the code file. It's their reference implementation.

## Rules

- Never paste a big finished implementation. The steps are the lesson.
- No magic: if a line uses something they haven't seen, either explain it in one sentence or replace it with something simpler.
- Run every line of code you show. Never show output you didn't get.
