---
type: Playbook
title: E2E Fixtures
description: "xberg's e2e fixture schema: fields, call names, input shapes, assertion types, skip, categories under fixtures/. Use when adding or editing an xberg e2e fixture; generation itself is the shared e2e-generation skill."
paths:
  - "fixtures/**"
  - "e2e/**"
x-ai-rulez:
  kind: skill
  id: e2e-fixtures
  metadata:
    name: e2e-fixtures
---

# xberg E2E Fixtures

One JSON object per file under `fixtures/<category>/`; the directory is the category.

- Fields: `id` (unique snake_case, becomes the test name), `call`, `description`, `docs` (`topic`, `title`,
  `description`, `side_effects`), `assertions`; optional `category`, `tags`, `input`, `config`, `args`, `skip`.
- `call`: `extract` (most fixtures), `extract_batch`, `pdf_page_count`, `extract_with_external_redaction`, and the
  plugin-registry calls (`list_*`, `register_*`, `unregister_*`, `clear_*` for OCR, embedding, tokenizer, reranker
  backends, renderers, validators, post-processors).
- `input`: `extract_input` (`kind: "uri"` with `$mock_url/...`, or `bytes` + `filename` + `mime_type`) plus
  `mock_responses` (`path`, `status_code`, `headers`, `body_file` relative to the repo, usually
  `../test_documents/...`); batch calls take `inputs`.
- `assertions` is a list of `{type, field, value}`. Types: `not_error`, `error`, `equals`, `min_length`, `count_min`,
  `count_equals`, `contains`, `contains_any`, `contains_all`, `not_contains`, `not_empty`, `greater_than_or_equal`,
  `less_than_or_equal`. `field` is a path into the result, e.g. `results[0].mime_type`.
- `skip`: `{languages: [...], reason: "..."}`.
- Categories: `smoke`, `extract`, `batch`, `contract`, `error`, `format_specific`, `pdf`, `images`, `code`, `url`,
  `plugin_api`, `registry`, `summarization`, `repros`.

Copy the nearest existing fixture of the same `call` rather than writing one from this list.
