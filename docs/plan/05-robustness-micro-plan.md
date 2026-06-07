# Plan 05 — Robustness Micro-Plan (typo tolerance, 10k+ fixtures)

Small chunks, each with a verification gate. `PY=.venv/bin/python`.

## CHUNK A — Fuzzy matching core (`ector/fuzzy.py`)
- Bounded Levenshtein (early-exit), length-relative threshold, candidate index
  bucketed by (first-letter, length), LRU cache.
- Unit tests `tests/test_fuzzy.py`.
- Gate: tests pass, lint clean.

## CHUNK B — Expanded currency data + misspellings
- Grow `dictionary/currencies.py`: more codes, symbols, slang, and a curated
  misspelling map; add spelled-out number words (en/fr) data.
- Gate: import + existing money tests still pass.

## CHUNK C — Number parsing robustness (`ector/money.py`)
- Decimal comma, thousand separators, "1k"/"2.5k", attached code "25usd".
- Spelled-out amounts (common), en/fr.
- Unit tests in `tests/test_money.py` (extend).
- Gate: tests pass.

## CHUNK D — Giga product/brand catalog (`dictionary/catalog.py`)
- Hundreds of e-commerce nouns + brands + categories (en/fr), canonical forms.
- Used by fuzzy normalization and by fixture generation.
- Gate: import + a uniqueness/normalization test.

## CHUNK E — Functional-vocabulary normalization (`ector/normalize.py`)
- Pre-spaCy pass: fuzzy-correct currencies, budget word, trigger verbs,
  connectors, units, and known catalog nouns/brands; leave unknowns intact.
- Unit tests `tests/test_normalize.py`.
- Gate: tests pass; existing integration tests still pass.

## CHUNK F — Token-based fallback extractor (`ector/products.py`)
- `extract_products_fallback(sentence/text, config)` that ignores dependency
  parse; classify+group content tokens.
- Wire into `api.extract_sync`: union with dependency results, dedupe by head.
- Gate: existing tests pass; new fallback unit tests pass.

## CHUNK G — Fixture generator (`tests/fixtures/generator.py`)
- Deterministic (seeded). Templates × catalog × currencies × typo profiles.
- Typo profiles: clean, single-edit, multi-edit, keyboard, transposition,
  casing/spacing, phonetic.
- Emits labelled cases (text, lang, expected products/price/currency/budget).
- Generate >= 10,000 cases to `tests/fixtures/dataset.jsonl` (committed).
- Gate: generator runs; dataset has >= 10000 lines.

## CHUNK H — Measurement harness (`tests/test_fixture_corpus.py`)
- Load dataset, run ECTOR, compute typo-tolerant match metrics, assert
  per-category thresholds. Print a summary report.
- Gate: harness runs end-to-end.

## CHUNK I — Iterate to targets
- Loop: run harness → inspect failures by category → fix extractor/dicts →
  re-run. Repeat until thresholds met. Record final numbers in status doc.

## CHUNK J — Performance pass
- Ensure 10k cases run in reasonable time (cache models, fuzzy caches,
  precompiled structures). Measure and record.

## CHUNK K — Docs + final hardening
- Update feature/status docs with final metrics; full lint+test; example+CLI.
