---
name: tinker-ai-skill
description: Turn your own coding-agent session transcripts (Claude Code JSONL) into a supervised fine-tuning dataset and train a LoRA on Tinker with the tinker-cookbook. Use when the user wants to fine-tune a model on their agent sessions, build an SFT dataset from transcripts, anonymize or de-identify transcripts, slice long sessions to a context length with compaction context, or train and evaluate on Tinker. Covers collection, cleaning (secrets, PII, paths), chunking, train/val splits, training, sampling, and the pitfalls that cost us runs.
license: MIT
compatibility: Python 3.11+, uv or pip, tinker-cookbook>=0.6.0 (installs tinker, torch, tml-renderers), a Tinker API key, optionally a Weights & Biases API key. Scripts run from the skill directory; dataset steps are offline, training and sampling call the Tinker service and cost money.
metadata:
  author: Migel Tissera
  version: "1.0.0"
  source: https://github.com/drost-ai/tinker-ai-skill
---

# Fine-tune a coding model on your own agent transcripts (Tinker)

You are helping someone turn the sessions they already ran with a coding agent into
training data, and fine-tune an open model on it with [Tinker](https://thinkingmachines.ai/tinker).
This skill distils a pipeline that shipped several public models. Follow the steps
in order; each script is small, offline unless stated, and prints what it did.

All commands below run from this skill's directory (`tinker-ai-skill`). Read `references/` when a step
needs judgement; the scripts' docstrings (`python scripts/<name>.py --help`) explain
every flag.

## Before you start

1. **Keep the transcripts.** Claude Code deletes transcripts after 30 days by default.
   Tell the user to add `"cleanupPeriodDays": 3650` to `~/.claude/settings.json` now.
2. **Keys.** Copy `.env.example` to `.env` and fill in `TINKER_API_KEY`
   (console at tinker.thinkingmachines.ai) and `WANDB_API_KEY` (wandb.ai/authorize).
   Never print, commit, or paste these values anywhere; the scripts read `.env`.
3. **Environment.** `uv venv && uv pip install -r requirements.txt` (or `pip install -r requirements.txt`).
   Python 3.11+. Use that interpreter for every script.
4. **Budget.** Training costs tokens x price. Always run a script's default (offline)
   mode first; only `--train`, `sample_checkpoint.py` and `export_checkpoint.py` touch
   the service. Confirm the estimated cost with the user before launching.
5. **For local serving (steps 8-9).** A built [llama.cpp](https://github.com/ggml-org/llama.cpp)
   checkout recent enough for the model's architecture, disk for the base model plus
   the merged copy (about 2 bytes per parameter each), and RAM for the largest shard.

## The workflow

### Step 1. Collect transcripts into a dataset location

```
python scripts/collect_sessions.py --data-dir ./data            # ~/.claude/projects by default
python scripts/collect_sessions.py --data-dir ./data --project my-repo --since 2026-01-01
```

Copies main-session files verbatim (no subagent sidechains), skips tiny sessions,
records sha256s in `data/originals/manifest.json`. Use `--exclude-slug` for projects
that must never leave the machine (client work, security research).

### Step 2. Clean: normalize, then remove secrets and identity

```
python scripts/normalize_sessions.py --data-dir ./data
python scripts/anonymize_sessions.py --data-dir ./data --identity-file identity.json
```

`normalize_sessions.py` turns the raw records into OpenAI-style messages: user text
the person typed, assistant text and plaintext thinking, tool calls with their JSON
arguments, tool results clipped to head+tail. It drops harness-injected text,
sidechains, API-error placeholders, thinking signatures and image bytes, and
verifies every tool call is answered. See `references/claude-code-transcripts.md`.

`anonymize_sessions.py` first replaces credentials by value across the whole corpus
(one marker per value), then de-identifies each session with its OWN random
identity: home username, top-level folders under the home directory, project slugs,
and every name/email/handle/org/domain listed in the identity file. Write that file
with the user (their username, full name, emails, GitHub handle, company). The run
fails if any listed string or credential candidate survives. Read the printed list
of detected usernames; pass `--keep-username` for service accounts that are not a
person. Why per-session randomization and not one fixed fake world:
`references/anonymization.md`.

Inspect a few anonymized rows with the user before continuing. Only the user can
judge whether something is still sensitive.

### Step 3-5. Slice to the context length, add compaction context, split train/val

```
python scripts/build_dataset.py --data-dir ./data --model Qwen/Qwen3.6-35B-A3B --max-len 65536 \
    --system-prompt-file assets/system-prompt.md
```

Pick `--model` from Tinker's model list and `--max-len` from that model's context
column (64K base variants; `:peft:262144` variants take 256K). The builder measures
every row with the real renderer and tokenizer of that model, so **rebuild when you
change models**: a tokenizer change moved our rows by 14% and overflowed the budget.

- Windows never split a tool call from its result and never open on a tool message.
- Slice 0 carries the system prompt plus the working directory. Every later slice
  carries the same prompt followed by a deterministic `<working_context>` block
  (original request, recent requests, files touched, commands, task state, a trace
  of the last few messages) and, when the window opens mid-turn, a short
  "continuation" user message. This is the compaction the model will see in a real
  long session. Details: `references/chunking-and-compaction.md`.
- Tool definitions are declared on every row. Pass `--tools-file` with the real
  definitions of the harness the model will serve in; without it, minimal schemas
  are inferred from usage. Rows without tool definitions regressed tool use for us.
- Hybrid-thinking renderers are rebuilt to keep thinking in history (otherwise
  earlier turns train on empty think blocks). For Inkling models pass `--effort`
  (default 0.9) and use the same value at serving time.
- The split is by whole session, seeded, so rebuilds hold out the same sessions.

Report: `data/datasets/<name>.report.json` (rows, tokens, loss tokens, sha256s,
rendering provenance). The trainer refuses a dataset whose provenance differs.

### Step 6. Fine-tune on Tinker

```
python scripts/train_tinker.py --data-dir ./data --name qwen3.6-35b-a3b-64k            # offline smoke test
python scripts/train_tinker.py --data-dir ./data --name qwen3.6-35b-a3b-64k --train    # launch
```

The smoke test renders every row, prints the decoded head of a row (read it: system
prompt, tool declaration, user turn), steps per epoch and total tokens. Multiply
tokens by the model's train price from Tinker's pricing page and tell the user the
estimate before `--train`.

Defaults: LoRA rank 32, batch 8 rows, 2 epochs, linear decay, eval and checkpoint
every 20 steps, W&B project `agent-transcript-sft`. Learning rate comes from
Tinker's calibrated `get_lr` for Qwen/Llama; for Inkling, Nemotron, DeepSeek, Kimi
and GLM you must pass `--learning-rate` (ranges and evidence in
`references/tinker-training.md`). When in doubt run two short runs, 1e-4 and 3e-4,
and compare behaviour, not loss.

While it runs: confirm the first metrics reach W&B, watch `test/nll` at steps 20 and
40 (a dip then a rise means the LR is too hot for this batch; stop and lower it),
and never wrap Tinker calls in your own timeouts or retries.

### Step 7. Check behaviour and pick a checkpoint

```
python scripts/sample_checkpoint.py --data-dir ./data --name qwen3.6-35b-a3b-64k \
    --checkpoint tinker://<run-id>/sampler_weights/000100 --prompt "Find and fix the failing test."
```

Compare base vs checkpoints on prompts from the user's real work. Judge by behaviour
(valid tool calls, non-empty thinking, follows the system prompt), not by NLL: a
falling loss hid a behaviour regression for us twice. Pick the checkpoint by an eval.

### Step 8. Download the LoRA and merge it into the base model

```
python scripts/export_checkpoint.py --run-dir ./runs/<run> --checkpoint 000100 \
    --base-model Qwen/Qwen3.6-35B-A3B --out ./export/my-coder --trust-remote-code
```

Reads `checkpoints.jsonl`, downloads the **training** checkpoint (sampler
checkpoints cannot be downloaded; periodic ones expire after 7 days, so export
before then), merges it with the cookbook's `build_hf_model` into a standalone bf16
HuggingFace directory, copies `generation_config.json`, and prints the chat-template
kwarg that restores the training conditioning (earlier-turn thinking kept).
`--peft` additionally writes a PEFT adapter for vLLM or SGLang. `--dry-run` shows
the plan without contacting Tinker. Details and memory needs:
`references/export-and-serve.md`.

### Step 9. Convert to GGUF and run with llama.cpp

```
LLAMA_CPP=~/src/llama.cpp scripts/make_gguf.sh ./export/my-coder/hf-merged ./export/my-coder/gguf my-coder Q4_K_M Q8_0
scripts/serve_gguf.sh ./export/my-coder/gguf/my-coder-Q4_K_M.gguf
```

`make_gguf.sh` converts to BF16 GGUF with the checkout's `convert_hf_to_gguf.py`,
quantizes with the `llama-quantize` built from the same commit, exports the vision
projector when the model has one, and optionally the MTP draft head (`MTP=1`).
`serve_gguf.sh` starts `llama-server` with the settings that match training:
`--jinja`, `--reasoning-preserve`, the template kwarg for preserved thinking, a
context of at least the training window, and the base model's sampling defaults
(temperature 1.0, top-p 0.95, top-k 20, min-p 0). Smoke-test one prompt with a
tool before trusting it, then benchmark against a same-recipe base GGUF.

## Rules that saved us the most time

- Never hardcode a renderer name; resolve it from the model with
  `model_info.get_recommended_renderer_name`. Never reuse a dataset rendered for one
  model with another model.
- Never anonymize with one constant fake world. Randomize per session.
- Never train rows without the system prompt and tool definitions the model will be
  served with.
- Never trust a loss curve alone. Sample.
- Never serve with a chat template that strips earlier-turn thinking when training
  kept it, and never with llama.cpp's default min-p: match the template kwarg and the
  base model's sampling defaults.
- Never put data, `.env`, run or export directories in a public repo: the pack's
  `.gitignore` covers `data/`, `runs/`, `export/`, `wandb/`, `.env`.

## Adapting to other agents

The normalizer reads Claude Code's JSONL. For Codex, OpenCode or your own harness,
write a normalizer that emits the same per-session file (`references/claude-code-transcripts.md`
documents the message schema); every later step is format-independent.
