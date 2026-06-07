# Plan 02 — Micro Plan (step-by-step with verification gates)

Every step lists: action, files, and the **gate** (command that must pass before
moving on). The suite must be green at every gate. `PYV=.venv/bin/python`.

## Conventions
- Gate-T: `.venv/bin/python -m pytest -q` → all pass.
- Gate-L: `.venv/bin/ruff check .` → no errors.
- Gate-E: `.venv/bin/python example.py` → runs, sane output.
- Gate-D: `.venv/bin/python scripts/diagnose_baseline.py` (used to confirm
  before/after behavior of specific bugs).

---

## STEP 0 — Baseline (DONE)
- Gate-T: 11 passed. Gate-D: all bugs confirmed.

## STEP 1 — Tooling config
1.1 Add `[tool.ruff]` and `[tool.pytest.ini_options]` to `pyproject.toml`.
- Gate-L, Gate-T.

## STEP 2 — `types.py`
2.1 Add `Product`, `Budget`, `ExtractResult` TypedDicts + `Price`/`Currency`
aliases.
- Gate-L, Gate-T (no behavior change).

## STEP 3 — `dictionary/` package (data move + repair)
3.1 Create `ector/dictionary/__init__.py` re-exporting existing names so old
imports keep working.
3.2 Create `currencies.py` (CURRENCY_MAP, MONEY/ CURRENCY_ONLY patterns).
3.3 Create `en.py`, `fr.py` with triggers/fillers/budget hints.
3.4 **Repair BUG-004** missing commas while moving.
3.5 Add a `_normalize(list)` that lowercases, strips, dedupes (preserving order),
and a `_validate` that asserts no doubled-token concatenations.
- Gate: `.venv/bin/python -c "import ector.dictionary"` imports clean.
- Gate-T (existing tests still pass; they import from `ector.dictionary`).

## STEP 4 — `money.py` (single source of truth)
4.1 Implement `parse_price(text, *, allow_bare=False)` returning `(float|None,
str|None)`; symbols on either side; normalize via CURRENCY_MAP.
4.2 Implement `is_currency_only(name) -> bool` (full match).
4.3 Unit tests `tests/test_money.py` per Feature 03 acceptance criteria.
- Gate-T including new money tests.

## STEP 5 — `models.py`
5.1 `get_model(model_name)` with `@lru_cache`; `clear_model_cache()`.
5.2 Missing-model error; opt-in `ECTOR_AUTO_DOWNLOAD` via `sys.executable`.
5.3 Test `tests/test_models.py`: spy on `spacy.load` to assert single load.
- Gate-T.

## STEP 6 — `languages.py`
6.1 `LanguageConfig` dataclass + registry for en/fr (model, triggers,
trigger_regex, fillers sorted longest-first, budget_hints, copula/expletive/
price-preposition sets).
6.2 `get_language(code)` default en.
6.3 Test `tests/test_languages.py`.
- Gate-T.

## STEP 7 — `text_utils.py`
7.1 `normalize_text(text)` that preserves apostrophes/decimals (**BUG-014**) and
only normalizes true sentence terminators (or returns text unchanged and relies
on spaCy segmentation — chosen approach documented inline).
7.2 `clean_phrase(phrase, fillers)` deterministic longest-match (**BUG-012**).
7.3 Tests `tests/test_text_utils.py`.
- Gate-T.

## STEP 8 — `triggers.py`
8.1 `contains_trigger(text, config)` using precompiled word-boundary regex
(**BUG-009**).
8.2 Test `tests/test_triggers.py` ("forget"/"awesome"/"budget" must NOT trigger
on `get`/`some`/`get`).
- Gate-T.

## STEP 9 — `products.py`
9.1 Port `find_main_product_tokens` (sync) using `LanguageConfig` dep/lemma hints
(**RISK-005**); fix docstring example (**BUG-011**).
9.2 Port `collect_product_phrase` (sync).
9.3 Quantity handling: detect leading `nummod` quantity, exclude from name and
from price (**BUG-010**).
9.4 Tests `tests/test_products.py`.
- Gate-T.

## STEP 10 — `budget.py`
10.1 `is_budget(text, config)` language-aware (**BUG-001**), word-boundary.
10.2 Budget assembly without requiring currency (**BUG-008**).
10.3 Tests `tests/test_budget.py`.
- Gate-T.

## STEP 11 — `api.py` (new orchestrator) + wire up
11.1 Implement `extract_sync(text, lang)` using steps 4–10.
11.2 Implement async `extract` wrapping `extract_sync`.
11.3 Fix result-schema docstring (**BUG-007**).
11.4 Repoint `ector/__init__.py` to `api`.
- Gate-T (the **existing** `tests/test_extract.py` must still pass), Gate-E.

## STEP 12 — Remove dead/old code
12.1 Delete `core.py` and `triggers_fillers.py` once `api.py` fully replaces them
and nothing imports them (**BUG-003**). Keep `dictionary` package.
- Gate: grep shows no imports of removed modules. Gate-T, Gate-L.

## STEP 13 — Apply remaining behavior fixes + regression tests
13.1 Add regression tests: pound cake (**RISK-009**), quantity (**BUG-010**),
FR budget (**BUG-001**), no-currency budget (**BUG-008**), FR elision
(**BUG-014**), trigger boundaries (**BUG-009**).
- Gate-T, Gate-D (re-run diagnostics → bugs now resolved).

## STEP 14 — CLI (Feature 07)
14.1 `cli.py` (argparse) + `__main__.py`; register `[project.scripts]`.
14.2 Test `tests/test_cli.py` (invoke `main` with args, capture stdout JSON).
- Gate-T; manual `python -m ector "..."`.

## STEP 15 — Packaging & CI
15.1 `pyproject.toml`: model extras (**BUG-015**), scripts, ruff/pytest config.
15.2 `.github/workflows/ci.yml`: install models, drop redundant `poetry add`
(**BUG-016**).
- Gate-L, Gate-T.

## STEP 16 — Docs sync
16.1 Update README to match real schema and add CLI usage + docs link.
16.2 Ensure `core.py` docstring schema fix is reflected (now in `api.py`).
- Final review.

## STEP 17 — Hardening loop
Repeat until clean, three consecutive times:
- Gate-L, Gate-T, Gate-E, Gate-D.
- Fix any regression immediately; re-run from the failing gate.

## Rollback strategy
Each step is a small, independently revertible edit. If a gate fails and a fix
isn't obvious within two attempts, revert the step, re-read the relevant audit
entry, and choose an alternate approach (documented in the step's notes).
