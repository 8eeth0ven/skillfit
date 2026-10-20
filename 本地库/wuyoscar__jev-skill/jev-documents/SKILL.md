---
name: jev-documents
description: Locate, select, extract and verify evidence in documents or observed code inventories. Use for source-span extraction, passage reranking, claim checks or choosing code locations to inspect. Preserve citations and no-match outcomes; use required graph tools for exact code lookup.
---

# Find and verify source evidence

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

## Choose the evidence workflow

- **Documents:** follow the workflow below for original spans, passage relevance
  and claim checks; adapt [the document template](assets/example.json).
- **Code locations:** read [code-location selection](references/find-code.md)
  and adapt [the code-location template](assets/find-code.json). Use the project's
  required graph/index tools first. Inspect selected code before making claims.
- **Judging whether a change is correct:** use `jev-eval` if installed, rather
  than treating a relevance score as a code-review result.

## Workflow

1. Read the authorized source and retain document/page/line identifiers. Have parsers or regex produce exact candidate spans when possible.
2. Define the requested role precisely: invoice destination is not any email address. Include none when no candidate fits.
3. Use independent relevance questions when ranking all passages; winning a relative Choice does not establish an answer exists.
4. Copy the original span selected by ID. Do not ask Jev to synthesize the extracted field or fabricate a quotation.
5. The host checks claims against their cited evidence and writes the synthesis; Jev may help screen many claims, not replace reading. Report unsupported/contradicted statements and preserve source links.

## Context and parallelism

Jev does not inherit the agent's history. Give every request sufficient context:
the user's information need, exact claim, source IDs, surrounding passages,
definitions and relevant exceptions. Supply the text, not just a URL or your own
summary verdict. Keep needed cross-references; omit unrelated material and secrets.

Batch independent claim checks or per-passage relevance scores over shared state
instead of serial LLM calls. For separate document groups, use bounded concurrency
with stable document/question IDs, rate limits and a cost/time budget. The host
schedules calls; the CLI has no parallel scheduler. Questions cannot read other
answers in the same request: fetch a selected source before asking about unseen
contents. Use Jev's low latency for repeated judgments, not document generation.

## Make it yours

Replace the example's evidence, candidate IDs and criteria together. Preserve a
no-match route when the real task can fall outside the labels. Agree on how the
host or person consumes each answer before enabling any automatic effect.

## Precedent

[Related project or author example](https://github.com/jkudish/jev-mcp). Our workflow is an adaptation,
not that project's code, an automatic installer, or a reproduced benchmark.
[OpenRouter request contract](https://openrouter.ai/docs/api/api-reference/alphadecisions/submit-a-decisions-questions-and-answers-request).

## Examples

[Rerank search and retrieval results](https://github.com/wuyoscar/jev-skill#sc-a19) · [Repository navigation](https://github.com/wuyoscar/jev-skill#sc-a20) · [Find meaning on a page, not just matching words](https://github.com/wuyoscar/jev-skill#sc-semantic-find)

[More workflows and local templates](references/scenarios.md). Browse across
examples when designing a solution; follow the guides and sources that help.
