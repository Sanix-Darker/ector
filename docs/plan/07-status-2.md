# Plan 07 — Status (Robustness, Richer Fields, Performance, Web)

State after the typo-tolerance + e-commerce-parser + web-showcase work.

## Quality (12,000-case deterministic corpus, `tests/fixtures/dataset.jsonl`)

| Metric | Rate |
|--------|------|
| Product item recall | 99.19% |
| Product precision | 97.37% |
| Product case recall (all items in a case) | 98.82% |
| Price accuracy | 98.07% |
| Currency accuracy | 97.89% |
| Budget accuracy | 94.22% |

Corpus throughput: ~490 cases/sec (full pipeline, warm cache).

Measure with: `.venv/bin/python scripts/measure.py`.

## Performance (`scripts/bench.py`, warm)

| Metric | Value |
|--------|-------|
| Throughput | ~450-490 calls/sec |
| Mean latency | ~2.2 ms |
| p50 | ~2.0 ms |
| p95 | ~3.1 ms |
| p99 | ~4.5 ms |

First call pays the spaCy model load (~200 ms); cached thereafter
(`functools.cache` in `models.py`). Disabling the unused `ner` pipe gave ~50%
throughput improvement.

## What was added

### Typo tolerance (Feature 08)
- `ector/fuzzy.py`: bounded Damerau-Levenshtein, length-relative thresholds,
  bucketed candidate index, caches.
- `ector/normalize.py`: pre-spaCy correction of closed-class/known vocabulary
  (currencies, budget word, triggers, connectors, catalog nouns/brands), with a
  common-word stop-list to avoid over-correction.
- Expanded `dictionary/currencies.py` (codes, symbols, slang, misspellings),
  `dictionary/numbers.py` (spelled-out amounts), `dictionary/catalog.py` (521+
  product/brand terms), `dictionary/common_words.py`, `dictionary/attributes.py`.
- Robust money parsing in `money.py`: thousands/decimal separators, "1k",
  glued/space-separated currency, fuzzy currency words, spelled-out amounts.
- `products.py`: parse-independent token fallback extractor; trigger-noun and
  attribute-word exclusion; conjunct recovery across price phrases.
- `api.py`: two-pass sentence reconciliation (price tails, split budget clauses);
  fallback augments dependency extraction (dedupe by head).

### Richer e-commerce fields (Feature 09)
- `ector/attributes.py`: brand, attributes, condition (typo-tolerant).
- `ector/constraints.py`: price constraints (max/min/around/between, en/fr).
- `ector/intent.py`: intent classification.
- `types.py` extended; `api.py` enriches products and adds `price_constraint` +
  `intent` (all additive; existing keys unchanged).

### Web showcase (`web/`)
- FastAPI app (`web/app.py`) + static UI (`web/static/`), optional `web` extra.
- Endpoints: `/api/health`, `/api/examples`, `/api/extract`, `/` + `/static`.
- TestClient smoke tests (`tests/test_web.py`).

### Testing
- 166 tests: unit (fuzzy, money, normalize, catalog, attributes, constraints,
  intent, triggers, budget, products, languages, text_utils, models), corpus
  threshold gate (`tests/test_fixture_corpus.py`), robustness/fuzz
  (`tests/test_robustness.py`), web smoke, doctests, and the original contract.

## Known residual gaps (acceptable, documented)
- Budget currency under very heavy currency-word typos ("buccws", "ouds") may be
  dropped (price still correct). ~2% of budget cases.
- Product modifiers are sometimes dropped under severe typos (head noun is still
  captured, which is what the metric and downstream search care about).
- Price attribution in multi-product sentences attaches one price to all
  products (documented RISK-002 policy).

## Reproduce
```bash
pip install -e ".[web,models]"
pip install pytest ruff httpx
ruff check .
pytest
python scripts/measure.py
python scripts/bench.py
```
