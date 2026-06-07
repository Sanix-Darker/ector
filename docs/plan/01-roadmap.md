# Plan 01 — Roadmap

Phased delivery. Each phase ends with a green test suite and a clean `ruff`.

## Phase 0 — Environment & baseline (DONE)
- Create venv (Python 3.12), install spaCy + models (worked around corporate SSL
  by pointing `REQUESTS_CA_BUNDLE` at the openssl bundle).
- Run existing tests → 11 passing.
- Empirically confirm catalogued bugs via `scripts/diagnose_baseline.py`.

## Phase 1 — Documentation (DONE in this pass)
- Overview, architecture, glossary.
- Audit (bugs, smells, risks).
- Feature specs (product, budget, money, multilingual, models, API, CLI).
- Fix plan, roadmap, micro-plan, refactor plan, test strategy + matrix.

## Phase 2 — Test scaffolding
- Add `tests/` for unit-level modules (money, triggers, products, budget,
  dictionary validation) reflecting target behavior.
- Keep existing `tests/test_extract.py` as the integration contract.
- Add pytest + ruff config to `pyproject.toml`.

## Phase 3 — Refactor (behavior-preserving)
- Create new modules: `types.py`, `text_utils.py`, `money.py`, `models.py`,
  `languages.py`, `triggers.py`, `products.py`, `budget.py`, `api.py`,
  `dictionary/` package.
- Re-point `ector/__init__.py` and `extract` to the new code.
- Keep old modules as thin shims until removal; suite stays green throughout.

## Phase 4 — Correctness fixes (intended behavior changes)
- BUG-001, 008, 009, 010, 012, 014, RISK-009.
- Add/adjust tests to pin new behavior.

## Phase 5 — Performance
- Model caching (BUG-005); measure repeated-call speedup.

## Phase 6 — Packaging, CLI, CI
- Declare model extras (BUG-015), add CLI (Feature 07), fix CI (BUG-016).
- Update README to match real behavior; add docs links.

## Phase 7 — Hardening loop
- Run full suite + ruff + example + diagnostics repeatedly; fix until clean.
- Final review against acceptance criteria in each feature doc.

## Exit criteria (project "feature-proof")
- `ruff check .` clean.
- `pytest` all green, including new regression tests.
- `python example.py` runs and prints sensible output for EN + FR.
- CLI works (`python -m ector ...`).
- Model loaded once and cached.
- README and docstrings match actual output schema.
