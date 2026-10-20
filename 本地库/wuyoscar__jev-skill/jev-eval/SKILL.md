---
name: jev-eval
description: Judge supplied outputs against explicit criteria, including code-change reviews and authorized safety evaluations. Use for evidence-backed review leads, rubric judgments, or batch, multi-turn and team transcript evaluation; not permission to merge or run targets.
---

# Evaluate outputs against evidence and criteria

Use this skill for judgments about existing outputs or observed behavior, not for
finding source locations (`jev-documents`) or assigning routine business labels (`jev-triage`).

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

## Pick the evaluation mode

- **Code review:** read [diff and test-evidence review](references/code-review.md)
  and adapt [the code-review template](assets/code-review.json). Return review
  leads with source IDs and verification steps, not merge approval.
- **Other output review:** define the user's rubric, supply the actual output and
  supporting evidence, and ask independent outcome/evidence questions. Let the
  host write task-specific integration and tests when requested.
- **Authorized safety evaluation:** continue to the safety workflow below; read
  only the relevant [batch, multi-turn or team protocol](references/workflows.md).
  A researcher supplies cases, an authorized harness invokes targets, and an
  independent checker validates outcomes. Jev does not generate attacks or grant scope.

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

## Context and checks

Jev does not inherit the agent's history. Give each judgment enough context:
the criteria, actual output, source evidence and missing facts. Put independent
outcome and evidence questions in the same request. Use bounded concurrency for
independent requests only; the host schedules them. Wait for new observations
before dependent checks. Review leads are not merge approval or proof of intent.

For captured safety-test transcripts, read [the safety workflow](references/safety.md)
only when needed. The host owns target authorization and execution; this skill
judges supplied evidence and does not expand the test scope.

## Examples

[Completion evidence check](https://github.com/wuyoscar/jev-skill#sc-a06) · [Detect unsupported success language](https://github.com/wuyoscar/jev-skill#sc-a07) · [Plan versus action](https://github.com/wuyoscar/jev-skill#sc-a03)

[More workflows and local templates](references/scenarios.md). Browse across
examples when designing a solution; follow the guides and sources that help.
