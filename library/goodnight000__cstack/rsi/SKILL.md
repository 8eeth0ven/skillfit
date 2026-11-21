---
name: rsi
description: Improve an agent's skills, instructions, tools, or working process through bounded before-and-after experiments. Use when asked to run agent self-improvement or test a proposed harness change; ordinary session reviews belong in Reflect.
---

# RSI

Improve how an agent works while keeping its underlying model fixed. Produce a tested change or an evidence-backed decision to keep the current version. Explain each proposed mechanism and why it should help in plain language.

This skill guides experiments; it supplies no runner, sandbox, scheduler, or spending enforcement. Use the project's existing tools. Writing instructions, passing file validation, and producing a persuasive reflection do not establish better task performance.

## 1. Bound the experiment

Carry forward the user's target, authorization, budget, and stopping point. Identify the maintained files and how the executing agent actually loads them. Distinguish a skill or tool defect from a model limitation, missing access, temporary outage, or changed requirement.

Before execution, record the editable scope, comparison task, model/settings, success criteria, protected behavior, cost/time or run cap, and adoption authority. Inspect available runners and evidence before asking the user for setup. State reasonable local defaults; ask only for a missing decision or authorization that materially blocks execution. Existing authorization covers work within those bounds without repeated approval. A review-only request stays review-only. Unspecified scope is not permission for an unattended campaign, paid services, publication, production changes, or global instruction edits.

Prefer one candidate addressing one mechanism. Use a predeclared stopping point for multiple rounds: the authorized budget, a bounded number of attempts without useful improvement, or unreliable evaluation. Ensure individual commands and runs terminate within the campaign's remaining budget.

## 2. Diagnose and predict

Reuse a current Reflect finding if its evidence still applies. Otherwise, when [Reflect](../reflect/SKILL.md) is installed, use its evidence reconstruction, guidance inspection, lesson selection, and destination routing. Run its full review workflow only when a review is requested. If unavailable, inspect the task, corrections, actual outcomes, relevant instructions, and previous changes directly.

Compare failed and successful executions of the same procedure when available. Establish what the agent knew at the time and whether the proposed cause recurs beyond one example. A single verified defect can justify a fix; uncertain causes remain hypotheses. If an existing rule was ignored, investigate its discovery and execution before adding another rule.

State the smallest candidate change, the outcome expected to improve, and a nearby situation it might harm or where it should not apply. Consider removing or narrowing guidance, repairing a tool, or changing when information is provided. Preserve failed ideas and their evidence so later rounds do not repeat them without a new reason.

## 3. Prepare a fair comparison

Preserve the current version. Stage the candidate in an isolated copy or worktree and confirm each arm loads its intended version. Keep starting state, model/version, tools, settings, and resource limits comparable. Reset task state between attempts so one arm cannot benefit from the other's work. Label unavoidable differences as limits on attribution.

Use separate cases for developing changes, selecting candidates, and final reporting. Choose final cases before seeing candidate results and keep them, their answers, and their results out of the optimizer's context during search. Freeze the candidate before the final comparison. Any feedback used for another edit becomes development or selection evidence, even if called a holdout. Previously exposed final cases cannot certify the next version as unseen-task progress. A small pilot without fresh final cases can establish local behavior only.

Define scoring from requested outcomes before examining the candidate's results. Use deterministic checks for mechanical facts. For judgment, use a fixed rubric and preferably blinded comparisons with presentation order balanced. Check actual outputs and user feedback; an agent judge's preference does not establish the user's taste or acceptance.

Keep scoring code, expected outcomes, protected data, and permissions outside the candidate's writable scope. Verify available isolation rather than treating a prompt or a separate reviewer name as enforcement. If isolation is unavailable, limit the experiment accordingly and disclose it. Repair a genuine grader defect separately, invalidate affected comparisons, and rerun both versions under the repaired grader.

## 4. Run and decide

Start with the smallest check that exercises the hypothesized mechanism. An unexercised tool path, broken environment, or invalid scenario must be resolved before broader runs. Reuse existing task checks; add only missing checks needed for this experiment.

Compare task completion and protected behavior, then the relevant time, cost, corrections, and complexity. Record every planned attempt, including failures and timeouts. Account for infrastructure failures consistently across arms. Report experiment cost separately from the resulting agent's operating cost. If a metric is unavailable, say so.

Use repeated runs where outcome variation could explain the proposed gain. Size them to the observed variation, effect, and budget; a single lucky pass is not reliable progress. Do not keep rerunning only the candidate until it wins. Include previously successful tasks and nearby counterexamples to expose regressions.

Accept a candidate only under the predefined criteria. A higher average cannot compensate for breaking protected behavior. Treat a tie or an inconclusive result as a reason to keep the current version, unless simplification itself was a predefined objective and preserved quality is supported. Reject task-specific answers or shortcuts that improve the score without improving the intended behavior.

For multiple candidates, select using development/selection evidence, then compare the frozen winner with the baseline on untouched final cases. Check combined changes together because individually useful edits can interfere. Report a failed final check honestly; further tuning needs fresh final evidence.

## 5. Adopt and retain evidence

Distinguish a winning experimental candidate from an installed, published, or deployed change. Apply only within the user's adoption authority and the tested scope. When adoption is already authorized, verify the maintained target has not changed, apply the candidate, check its loading path, and retain a rollback version. Otherwise present the concrete diff and results for approval. Do not promote through an intervening conflicting edit.

Keep one concise record in the project's existing experiment notes or session artifacts: baseline/candidate versions, evidence, prediction, diff, task split, settings, commands, all outcomes, cost, decision, and rollback pointer. Keep private traces local and link to them instead of copying them into reusable skills. Include rejected candidates and why they failed. Use later real work to confirm or weaken the original hypothesis; avoid claiming general improvement from a narrow comparison.

## Improving the improver

When the target is Reflect, RSI, or the proposal process itself, freeze the scoring and adoption rules outside that candidate's control. Compare the old and new improvement procedures on the same fresh problem batches with equal budgets. Judge the downstream changes they produce by externally checked task results, regressions, and cost. More proposals, more persuasive explanations, or a better task agent alone do not prove a better improvement process.

State separately what was implemented, what the experiment established, what was adopted, and what remains unknown. If evaluation cannot distinguish progress from noise or the budget is exhausted, preserve the current version and report the exact uncertainty.
