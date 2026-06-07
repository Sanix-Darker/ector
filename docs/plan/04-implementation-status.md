# Plan 04 — Implementation Status

Final state after executing the micro-plan. All gates green.

## Summary
- **Tests:** 86 passing (unit + component + integration + CLI + doctests).
- **Lint:** `ruff check .` clean.
- **Example:** `python example.py` runs cleanly for EN + FR.
- **Diagnostics:** `scripts/diagnose_baseline.py` shows every confirmed bug resolved.
- **Performance:** model loaded once and cached (first call ~220ms incl. load,
  subsequent calls ~2ms; cache shows 20 hits / 1 miss in the timing probe).
- **Packaging:** wheel builds with the `dictionary/` subpackage and the `ector`
  console-script entry point; model extras declared.

## Module map (delivered)
| Module | Responsibility |
|--------|----------------|
| `ector/__init__.py` | Public API: `extract`, `extract_sync`, `__version__` |
| `ector/__main__.py` | `python -m ector` -> CLI |
| `ector/api.py` | Orchestration: `extract_sync` + async `extract` |
| `ector/types.py` | `Product`, `Budget`, `ExtractResult` TypedDicts |
| `ector/text_utils.py` | `normalize_text` (BUG-014), `clean_phrase` (BUG-012) |
| `ector/money.py` | `parse_price`, `is_currency_only` (BUG-002/003/010, RISK-009) |
| `ector/models.py` | `get_model` cached loader (BUG-005/006) |
| `ector/languages.py` | `LanguageConfig` registry + word-boundary trigger regex |
| `ector/triggers.py` | `contains_trigger` (BUG-009) |
| `ector/products.py` | token discovery, phrase building, quantity (RISK-005, BUG-010/011) |
| `ector/budget.py` | `is_budget` (BUG-001), `build_budget` (BUG-008) |
| `ector/cli.py` | argparse CLI (Feature 07) |
| `ector/dictionary/` | data package: `currencies`, `en`, `fr` + normalize/validate (BUG-004/013) |

## Removed (dead code)
- `ector/core.py` (god module) — replaced by `api.py` + focused modules.
- `ector/triggers_fillers.py` — split into `models.py`, `languages.py`, `money.py`.
- `ector/dictionary.py` (single file) — replaced by the `dictionary/` package.

## Behavioral changes vs. original (intentional, tested)
1. `My budget is 300` (no currency) → now emits `budget {price: 300.0}` (BUG-008).
2. `je n'ai que 50 euros` (fr) → now detected as budget (BUG-001).
3. `I want 2 phones` → product "Phones" + `quantity: 2`, no bogus price (BUG-010).
4. `I want a pound cake` → product kept (was dropped) (RISK-009).
5. `I want a smartphone for 200 USD` → name "Smartphone" (was "Smartphone for").
6. `at 150 usd max` → no spurious "Usd max" product.
7. French conjunction "iPhone ... et des Jordans" → both products extracted.

## Tooling notes (environment)
- Dev env: Python 3.12 venv. spaCy + models installed.
- Behind a corporate TLS proxy, spaCy's model downloader needed
  `REQUESTS_CA_BUNDLE`/`SSL_CERT_FILE` pointed at the system openssl bundle
  (`/opt/homebrew/etc/openssl@3/cert.pem`) since the bundled `certifi` lacked the
  proxy's root CA. pip itself worked without this. Documented for reproducibility.
- Newer `typer` dropped a bundled `click` that spaCy's CLI imports; installing
  `click>=8.1` resolved the model-download command.

## How to verify locally
```bash
.venv/bin/ruff check .
.venv/bin/python -m pytest
.venv/bin/python example.py
.venv/bin/python scripts/diagnose_baseline.py
.venv/bin/python -m ector "I want a laptop for 150 usd, budget 200 eur"
```
