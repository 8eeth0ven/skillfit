---
name: paper-to-runnable
description: Turn a research paper (arXiv id, arXiv URL or local PDF) into the smallest honest working implementation of its core idea, checked with a sanity ladder and a toy reproduction of the paper's main result, plus plots or an animation of what happens inside and a short explainer. Use when the user says "implement this paper", "reproduce this paper", "explain this paper by building it", "code up this arXiv paper", "make this paper runnable", "does this paper's result hold", or pastes an arXiv link and wants to understand how it works.
---

# Paper to runnable

A paper is a claim. The way to understand it is to find the one mechanism the claim rests on, build only that, and watch it produce the paper's result at toy scale. Everything else in the paper is supporting detail.

The output is a folder with five things: `notes.md`, one code file, a sanity ladder that passes, a toy result next to the paper's figure, and visuals plus `explainer.md`. A full worked example (Grokking, arXiv 2201.02177) is in `examples/grokking/` and walked through in `reference.md`. Read it before the first build.

## Setup

```
sh <skill>/setup.sh          # .venv with numpy, matplotlib, pypdf
sh <skill>/setup.sh torch    # only if the build truly needs autograd
PY=<skill>/.venv/bin/python
```

Check first: if the system `python3` already has numpy and matplotlib, it can be used instead. Default to numpy. Reach for PyTorch only when hand-written backprop would be longer than the idea itself (a multi-layer transformer, a conv net). ffmpeg comes from `$FFMPEG` or `ffmpeg` on the PATH.

## 1. Fetch the paper

```
python3 <skill>/scripts/fetch_paper.py <arxiv id | arxiv url | local.pdf> --out <work>/paper
```

It writes `paper.txt`, `meta.json`, the LaTeX `source/` and `equations.md` (every display equation with its number, label and source line, plus the author's macros). LaTeX gives exact equations, so read `equations.md` over the PDF text for math. If a paper has no numbered equations, the script says so: cite sections, figures, algorithms and appendix tables instead.

The script only downloads from arXiv. For any other link, ask the user before downloading anything, then pass the local PDF.

## 2. Find the core claim, write `notes.md`

Read the abstract, the figure captions, the main method section and the experiment setup (usually an appendix). Then write `notes.md` with these headings:

- **Claim**: one sentence, falsifiable. "X causes Y under Z."
- **Mechanism**: the one thing that makes it work. If removing it should break the result, it is the mechanism.
- **Equations to code**: a table of each equation used, its number, and the variable names it becomes.
- **Result to reproduce**: which figure or table, and what qualitative shape counts as success. Decide this before running anything.
- **Ablation**: the one switch that turns the mechanism off. This is the experiment that proves the mechanism matters.
- **Not reproduced, and why**: scale, architecture swaps, datasets, extra experiments. Be specific.

Show the user the claim, the mechanism and the planned result before writing code. They may know what they care about.

## 3. Build the minimal version

One file, under about 300 lines, from scratch. Every line that implements part of the paper gets a comment citing it: `# Eq. 3`, `# Sec 4.2`, `# A.1.2: lr 1e-3, wd 1`. Use the paper's hyperparameters where they are given. When you swap something out (a smaller model, a different task variant), say so in a comment at the swap and in `notes.md`.

Keep the paper's names for variables where they are readable (`Q, K, V`, `beta`, `alpha`). Write the backward pass by hand in numpy when it is short, because that is where understanding comes from.

## 4. Verify with a sanity ladder, then the toy result

Put the ladder behind a `--check` flag and run it before any long run. Each rung must pass before the next:

1. **Shapes**: every tensor has the shape the paper implies. Check the data generator against a few hand-computed examples.
2. **Gradient check** (if you wrote gradients): analytic versus central finite differences in float64, worst relative error under 1e-5.
3. **Overfit one small batch**: loss goes near zero, accuracy reaches 100%. If it cannot, the model or optimiser is broken.
4. **Chance at init**: the untrained model scores near chance. If it doesn't, there is leakage.
5. **Toy result**: the main run and the ablation, same seed, same budget. Report the numbers that define the result (for example "train 99% at step 1700, validation 99% at step 6100; with the switch off, validation stays at 0%").

Aim for a full run under a few minutes on CPU. Shrink the problem, not the idea. If the qualitative result does not appear, try the paper's settings first, then do a small sweep, and report what you tried. Never tune until it works and then hide the sweep: list every setting tried in `notes.md`.

Be honest about gaps. Write down what matched, what did not, and what the toy cannot tell us.

## 5. Visualise the internals, write `explainer.md`

Curves show that it works. Internals show why. Plot the quantity the mechanism acts on (attention weights, an embedding, a loss landscape slice, a hidden state over time) as training goes, with the mechanism on and off side by side.

For motion, use the helper. It writes PNG frames and stitches them with ffmpeg:

```python
sys.path.insert(0, "<skill>/scripts"); from animate import animate
animate(draw, n_frames, "out/mechanism.mp4", fps=12, size=(13, 7), preview=True)  # look first
```

Render with `preview=True` first, open one frame from the `_frames/` folder, then render full size. Look at the output image yourself before describing it.

Then write `explainer.md`: one question, one story, one lesson, about 300 words, plain words, for a smart reader who has not read the paper. The story is what the visual shows happening. End with what the toy does not show.

## Rules

- Run everything you show. Never quote a number you did not get.
- The ablation is not optional. Without it you have a training curve, not evidence.
- A toy reproduction supports the mechanism, not the paper's exact numbers. Say so.
- If the result fails to reproduce after honest effort, that is a valid outcome. Report it with what you tried.
