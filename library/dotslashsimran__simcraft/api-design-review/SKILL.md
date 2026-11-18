---
name: api-design-review
description: Review the design of an API surface, meaning an HTTP API (OpenAPI spec or route code), an SDK's public classes and functions, or a CLI. Checks naming and consistency, resource modelling, error design (stable codes, RFC 9457 problem details, request ids), versioning and breaking changes, pagination, filtering, idempotency and retries, rate limits, timeouts, long-running operations, webhooks, auth, partial updates, ID, time and money formats, SDK ergonomics and CLI conventions. Uses scripts to lint OpenAPI files, classify changes between two spec versions as breaking or safe, and dump an SDK's public surface. Writes review.md with a scorecard, ranked findings with rewrites, a breaking-change risk list and what is good. Use when the user says "review my API", "API design", "is this a breaking change", "OpenAPI review", "check my spec", "SDK ergonomics", "review my SDK", "review my CLI", or asks whether an API change is safe to ship. For onboarding and time to first success, use dx-audit instead.
---

# API design review

This skill reviews the shape of an API, which is the names, resources, errors, formats and rules that every user has to learn. Most API design mistakes are cheap to fix before launch and expensive after it, because fixing them breaks clients. The review therefore puts the findings that would be breaking to fix later at the top.

The judgement lives in `reference.md`, which has the scoring rubric, the severity scale, the rules for each area with citations to public guidelines (Google AIP, Microsoft REST API Guidelines, Stripe's API conventions, Zalando RESTful API Guidelines, IETF RFCs), and before and after rewrites. Read the sections that match the API before writing findings.

The scripts need only Python 3.9 or newer and the standard library. They read JSON, and they read YAML with PyYAML if it is installed or with a small built-in parser if it is not. Files that use YAML anchors or tags need PyYAML or a JSON copy.

## 1. Find out what to review

Ask one question at a time, and only for what is missing:

- **What is the surface?** It can be an OpenAPI file, route code, an SDK (a Python package name or a `.d.ts` file), or a CLI (`--help` output or the command source).
- **Who uses it?** Public, partner, or internal with one client. This sets severity (reference.md section 2).
- **Is it launched?** Before launch, recommend breaking fixes freely. After launch, every fix must come with a migration path.
- **Is there an old version to compare against?** If yes, run the diff in step 3.

## 2. Run the tools

Set `S=~/simcraft/skills/coding/api-design-review/scripts`.

**OpenAPI lint:**
```
python3 $S/lint_openapi.py openapi.yaml            # text
python3 $S/lint_openapi.py openapi.yaml --format md
python3 $S/lint_openapi.py openapi.yaml --fail-on high   # exit 1 for CI
```
It checks path and field case consistency, plural collections, verbs in paths, error schemas (missing, inconsistent, no machine code, no request id), undocumented 4xx and 5xx, list endpoints with no pagination or a bare array response, mixed ID and time formats, money as floats, creating POSTs without an Idempotency-Key, PATCH bodies with required fields, 429 without Retry-After, duplicate or missing operationIds, and unsigned webhooks.

**SDK surface:**
```
python3 $S/sdk_surface.py my_package [--path src] [--depth 2]
python3 $S/sdk_surface.py dist/index.d.ts
```
It prints the public tree (modules, classes, signatures, properties, constants) and hints about boolean flag arguments, long positional parameter lists, mutable defaults, `any`, optional parameters before required ones, timeouts that default to waiting forever, error classes with no common base, and missing docs. Importing a Python package runs its import code, so only run it on code the user trusts.

**For a CLI**, there is no script. Run `<tool> --help` and the help for each subcommand, try one command with `--json` and with output piped to a file, check the exit code after a failing command (`echo $?`), and compare against reference.md section 17.

**For route code with no spec**, export a spec if the framework can (reference.md section 18). Otherwise build the endpoint list by reading the routes.

The scripts find patterns, and they also produce false positives. Read every finding, drop the ones that are wrong for this API, and say which areas the scripts cannot check (behaviour, defaults, docs quality, real latency).

## 3. Check breaking changes

When there are two versions:
```
python3 $S/breaking_diff.py old.json new.yaml [--format md]
```
It sorts every change into BREAKING, RISKY or SAFE, says why, shows where changed shared schemas are used, and says what semver bump the changes need. It exits 1 if anything is breaking, so it can run in CI on every pull request.

The script cannot see behaviour changes such as a new default value, a different sort order, stricter server-side validation that the spec does not show, or new side effects. Ask about those directly.

When there is only one version, write the breaking-change risk list from the lint instead. It lists the findings whose fix would itself be breaking (bare array lists, integer IDs, missing pagination, error shape, field renames), so the user knows what to fix before launch.

## 4. Write review.md

Write `review.md` next to the API source unless the user says otherwise. Use this structure, and see `examples/review.md` for a full example:

1. **Summary.** Two or three sentences with the overall verdict and the top three fixes.
2. **Scorecard.** A table with each area from the reference.md rubric, a 0 to 3 score, and one line of reason. Mark areas that do not apply as n/a.
3. **Findings, ranked by severity (P0 to P3).** For each finding, give where it is, what is wrong, why it costs users something, the precedent from a public guideline, and a concrete rewrite (before and after for the path, schema, error body or call site). Group repeated cases into one finding with a list of locations.
4. **Breaking-change risk list.** Diff results if there were two versions. Otherwise, the fixes from the findings that would break clients, each with a migration path (alias, deprecation header, sunset date, new version).
5. **What's good.** Specific things the API does well, so the team keeps doing them. Write this section honestly and specifically, with no padding.
6. **Not checked.** What the review could not see.

Keep findings concrete. "Errors are inconsistent" is not a finding. "`POST /orders` returns `{error: {msg}}` and `GET /orders/{id}` returns `{message}`, so clients need two error handlers" is a finding.

## 5. Hand over

Show the user the summary and the top findings in chat, and give the path to `review.md`. If they want to fix things, start with the P0 findings, then the P1 findings that are breaking, and re-run the lint and the diff after each change.
