---
name: jev-triage
description: Use for user-defined inbox, support-ticket, feedback or record classification and prioritization, especially bulk parallel judgments with sufficient per-record context. Accepts smoke_test to have the host agent write and validate a task-specific paired pilot before bulk work. Produces labels and review queues, not replies or automatic mailbox changes.
---

# Sort messages and records by custom criteria

## Learn from the workflows

For design requests, browse the [scenario index](references/scenarios.md), read
the relevant guides and input/output examples, and compare or combine patterns.
Adapt what you learn to the user's task; the collection is inspiration, not a
closed menu. A familiar, straightforward decision can use its recipe directly.

Friendly reminder: Jev can help with initial, repeated or bulk judgments while
you lead the overall work. Read the evidence, design the workflow, spot-check
results (including confident or agreeing labels), and bring your own analysis
and synthesis. This is guidance for collaboration, not an agent harness or a
fixed call/token quota; existing user permissions and budgets still apply.

## 🚦 Before bulk work: `smoke_test`

Default `smoke_test=true` for large labeling jobs. This is an instruction to the
**host agent to write task-specific code**, not a Jev API field or a required
bundled runner. Accept it in a natural-language request or the host's supported
skill invocation arguments; never shell-evaluate raw argument text.

Read [the pilot workflow](references/smoke-test.md). Agree sample scope and model
IDs, write the sampling and bounded concurrent paired-call code for this user's
app, test it locally, then run the approved pilot. Both arms receive the same full
relevant context and criteria; keep independent gold labels out of both inputs.
Show actual IO, disagreements, coverage, failures and costs. Without gold, call
it agreement, not accuracy. Stop for review before scaling; a successful pilot
is not permission to label the full population or modify accounts.

`smoke_test=false` is an explicit user waiver, recorded as skipped, never passed.
In simulation mode do not invent a paired API result. Offer real setup or a waiver
and wait. See the reference for copyable prompts and optional task parameters.

## Use safely

Choose the service once and keep that choice. If unset, ask **A: real Jev** via
OpenRouter (`OPENROUTER_API_KEY`) or TypeSafe (`TYPESAFE_API_KEY`), or **B: simulation**
with this agent or an explicitly chosen available model such as DeepSeek. Wait for
consent; errors do not authorize switching. Check key presence only, never values.
Real calls send evidence and cost money; get approval before sending private data.

For B, skip CLI/API calls. Mark `agent_simulation` or `model_simulation`, identify
the actual model when available, set `jev_called: false`, `probability: null` and
`confidence: null`. Return a value, evidence-based reason and `needs_review`; use
null/review when evidence is missing. Do not invent Jev output or probabilities.
Choice uses supplied labels, Noul uses booleans, Score uses integer rubric indices.

For A, use the existing `jev-decide` CLI with the chosen `--provider openrouter`
or `--provider typesafe`. If absent, explain the dependency; do not silently install.
`--dry-run` is offline validation, not a judgment. Exit 0 means selected/scored,
2 means review, 1 means error. Read each value: false Noul remains false. Selection
is not permission, and confidence is not accuracy. Keep unknown/review paths.

## First request

Adapt [the example](assets/example.json). The shared CLI needs Python 3.10+;
no sibling skill is needed. Host tools still own collection and actions.
Resolve `<skill-dir>` to this installed folder:

```bash
jev-decide decide <skill-dir>/assets/example.json --dry-run
# After approval, send the edited request with the selected provider:
jev-decide decide /path/to/request.json --provider openrouter
```

## Workflow

1. Agree on categories with short inclusions/exclusions. Use independent Nouls when records can have several labels; use Choice for one queue.
2. Preserve original record IDs. For multiple records, name the exact record ID in every question or send one request per record; one Choice over an entire inbox is not per-message classification.
3. Collect text only from files or accounts the user authorized. Classify before writing tags, moving messages or sending replies.
4. Return a reviewable table: record ID, category, urgency, uncertainty and intended next consumer. Keep other/missing-evidence records visible.
5. Before bulk work, apply `smoke_test` above. Include near-miss categories and user-labeled examples; retest when criteria, models or context organization change.

## Context and parallelism

Jev does not inherit the agent's history. Give every request sufficient context:
the user's categories and priority policy, each record's text and relevant thread,
product/account facts, and known missing evidence. A last-message fragment is not
enough when earlier messages change its meaning; omit unrelated history and secrets.

For bulk triage, batch independent category, escalation and urgency questions over
shared state instead of serial LLM calls. Name the record ID in every question.
Use bounded concurrency for independent requests, with stable IDs, rate limits and
a cost/time budget. The host schedules calls; the CLI has no parallel scheduler.
Questions cannot read other answers in the same request: gather any newly needed
account evidence before a dependent follow-up. Low latency is a reason to use Jev
for the judgment stage, not to skip quality checks or automate mailbox changes.

## Make it yours

Replace the example's evidence, candidate IDs and criteria together. Preserve a
no-match route when the real task can fall outside the labels. Agree on how the
host or person consumes each answer before enabling any automatic effect.

## Precedent

[Related project or author example](https://github.com/sharziki/semdecide). Our workflow is an adaptation,
not that project's code, an automatic installer, or a reproduced benchmark.
[OpenRouter request contract](https://openrouter.ai/docs/api/api-reference/alphadecisions/submit-a-decisions-questions-and-answers-request).

## Examples

[Mark sponsor segments in a video](https://github.com/wuyoscar/jev-skill#sc-sponsor-skip) · [Support queue routing](https://github.com/wuyoscar/jev-skill#sc-h02) · [Urgency screening](https://github.com/wuyoscar/jev-skill#sc-h03)

[More workflows and local templates](references/scenarios.md). Browse across
examples when designing a solution; follow the guides and sources that help.
