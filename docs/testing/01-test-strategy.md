# Testing 01 — Strategy

## Principles
- The existing `tests/test_extract.py` is the **integration contract**. It must
  stay green through the refactor (Phases 2–3), and only change where an audit
  item deliberately changes behavior (documented in `fixes/01-fix-plan.md`).
- Add **unit tests** per new module so failures localize quickly.
- Add **regression tests** for every confirmed bug and risk, asserting the
  post-fix expected output.
- Tests must be deterministic and not require network (models installed once in
  the environment / CI).

## Layers
1. **Unit** — pure functions: `money`, `text_utils`, `triggers`, `dictionary`
   validation, `languages`. Fast, no model needed where possible.
2. **Component** — `products`, `budget` against real spaCy docs (needs models).
3. **Integration** — `extract` / `extract_sync` end to end (EN + FR).
4. **Performance** — model caching spy test (no second `spacy.load`).
5. **CLI** — invoke `cli.main` with argv, capture stdout JSON.

## Tooling
- `pytest` (configured in `pyproject.toml`).
- `ruff` for lint; CI runs both.
- Optional: doctest for corrected docstring examples.

## Determinism & models
- Models `en_core_web_sm` / `fr_core_news_sm` are required for component/
  integration tests. CI installs them explicitly (BUG-016 fix).
- Unit tests for `money`/`triggers`/`dictionary` avoid loading models.

## Definition of done (testing)
- All unit + component + integration + CLI tests pass.
- `ruff check .` clean.
- Diagnostics script shows all previously-confirmed bugs resolved.
