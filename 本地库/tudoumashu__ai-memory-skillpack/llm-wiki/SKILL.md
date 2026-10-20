---
name: llm-wiki
description: Query and maintain the user's local LLM Wiki from any Codex or Claude Code conversation or project. Use when the user asks to search personal knowledge, recall prior research or decisions, answer from the wiki, create durable notes, ingest a source into the wiki, update topic/concept/entity/question pages, write back useful answers, or run wiki lint/reindex workflows.
---

# LLM Wiki

## Core Rule

Use the local LLM Wiki as the durable knowledge source. Do not copy the wiki into this skill.

Paths on this machine:

```text
VAULT_ROOT=/home/shiyi/Apps/Obsidian/vault
WIKI_ROOT=/home/shiyi/Apps/Obsidian/vault/60-Wiki
INDEX=/home/shiyi/Apps/Obsidian/vault/60-Wiki/index.md
LOG=/home/shiyi/Apps/Obsidian/vault/60-Wiki/log.md
QUERY=/home/shiyi/Apps/Obsidian/vault/70-System/scripts/query_wiki.sh
LINT=/home/shiyi/Apps/Obsidian/vault/70-System/scripts/lint_wiki.sh
REINDEX=/home/shiyi/Apps/Obsidian/vault/70-System/scripts/reindex_qmd.sh
EMBED_SAFE=/home/shiyi/Apps/Obsidian/vault/70-System/scripts/embed_qmd_safe.sh
```

Default wiki prose to Chinese. Keep commands, paths, filenames, config keys, API fields, code, package names, versions, URLs, and fixed English terms unchanged.

## Obsidian Markdown Rules

Apply when creating or editing Markdown inside `VAULT_ROOT`, especially `WIKI_ROOT`.

- Preserve existing YAML frontmatter. New wiki pages use the local schema keys: `title`, `created`, `updated`, `kind`, `status`, `source_paths`, `tags`, `summary`.
- Every agent edit sets frontmatter `updated_by:` to the fixed actor string `claude-code/fable-5` or `codex/gpt-5.6-sol-pro`, and refreshes `updated`.
- Do not translate or rewrite frontmatter keys, wikilink targets, block IDs, embed targets, file paths, URLs, code blocks, JSON, or shell commands.
- Use `[[wikilinks]]` for internal vault notes (`[[path|display]]` for Chinese labels); normal Markdown links for external URLs.
- Prefer linking related `source` / `topic` / `concept` / `entity` / `question` pages over leaving isolated notes.
- Embeds `![[...]]`, callouts, `%% comments %%`, Mermaid, math, footnotes: only when they add durable structure or evidence. Tags live in frontmatter `tags`, not inline.
- After editing wiki Markdown, run `lint_wiki.sh`.

## Query Workflow

1. Start from `60-Wiki/index.md`.
2. If the query mentions a local project name or repo path, read the central project entity in `60-Wiki/entities/` first. Do not assume the entity file name matches the project name — locate it first with `rg -ilF "<project-name-or-repo-path>" /home/shiyi/Apps/Obsidian/vault/60-Wiki/entities/`; on multiple hits pick the page whose frontmatter `source_paths` contains the repo root (a body mention does not count, same criterion as `$ai-project-memory`), then read that page.
3. If the entity points to a repo `docs/ai/`, follow project read discipline — full read only `project-card.md` and `handoff.md`; targeted `rg` for `architecture.md`, `runbook.md`, `gotchas.md`, `diagrams/README.md`, current ADRs in `decisions/`; do not read `history/`, `reports/`, `screenshots/`, `learning/`, superseded ADRs (`Status: superseded/deprecated`), or deprecated ledger files by default(change-log 已停用 2026-07-28,git 提交即账本); on explicit user recall, targeted reads are allowed with cross-checking against current code.
4. Query the compiled wiki:

```bash
/home/shiyi/Apps/Obsidian/vault/70-System/scripts/query_wiki.sh "<query>" --scope wiki
```

5. If insufficient, widen scope:

```bash
/home/shiyi/Apps/Obsidian/vault/70-System/scripts/query_wiki.sh "<query>"
/home/shiyi/Apps/Obsidian/vault/70-System/scripts/query_wiki.sh "<query>" --scope raw
```

6. Read cited wiki pages directly before making important claims.
7. If wiki evidence is stale or insufficient, say so and use source pages, raw sources, project-local `docs/ai/`, or current web search when required.

## Writeback Workflow

Write back only when the answer or change has durable value. Choose the smallest correct destination:

- `60-Wiki/questions/`: reusable answer. `60-Wiki/topics/`: cross-source synthesis. `60-Wiki/concepts/`: reusable method, pattern, term. `60-Wiki/entities/`: person, company, tool, project, system. `60-Wiki/sources/`: single-source summary.

When writing back:

1. Prefer updating an existing page over creating a duplicate.
2. Preserve frontmatter and wikilinks; set `updated_by` per the rule above.
3. Add or update `source_paths`; link related pages.
4. Update `60-Wiki/index.md` when navigation changes.
5. `log.md` is newest-first: agents log **content changes only**(ingest、writeback、页面重构)by inserting a `## [YYYY-MM-DD] <kind> | <slug>` entry above the first existing `## ` heading. Never hand-write query or lint entries; `lint_wiki.sh` itself inserts a daily `lint | wiki-health` entry and writes a report under `70-System/reports/` — tool behavior, not a violation; do not remove those entries.
6. Keep uncertainty explicit with `inferred`, `unknown`, or open questions.
7. Never write secret values into any wiki page.
8. The vault is a git repository — after content writebacks, commit with an explicit file list including lint by-products(the updated `log.md` and the new `70-System/reports/wiki-lint-<date>.md`)(git 即账本,不积压未提交改动).

For a user-owned project with repo-local `docs/ai/`, the central project entity stays lightweight and points to the repo pack: repo path, `docs/ai/` path, key file links, short summary, important gaps. Never copy full `docs/ai/` content into the wiki; sync only on entity-level changes.

## Ingest Workflow

1. Read the source.
2. Create or update a source page in `60-Wiki/sources/`.
3. Extract durable points; update relevant topic / concept / entity / question pages — do not stop after only a source page when clear updates exist.
4. Update `60-Wiki/index.md`; add a content entry to `60-Wiki/log.md` per Writeback rule 5(newest-first, same header format).
5. Run lint and reindex.

## Validation

```bash
/home/shiyi/Apps/Obsidian/vault/70-System/scripts/lint_wiki.sh
/home/shiyi/Apps/Obsidian/vault/70-System/scripts/reindex_qmd.sh llm-wiki
```

Lint is required after any wiki edit. Reindex only when future search should find new or changed Markdown. Do not run `qmd embed` by default; run embedding only for immediate vector-search freshness or batch maintenance:

```bash
/home/shiyi/Apps/Obsidian/vault/70-System/scripts/embed_qmd_safe.sh llm-wiki
```

Avoid `npx --yes @tobilu/qmd ... embed`(version drift, startup cost). Large high-churn files(central `log.md`, project `handoff.md`, generated reports)cause repeated expensive embedding — keep entities lightweight and avoid embedding large dumps when a link is enough. Status check: `QMD_LLAMA_GPU=false qmd --index llm-wiki status`.

## Final Response

Mention: wiki pages read; wiki pages changed; validation commands run; any source gaps, uncertainty, or stale information.
