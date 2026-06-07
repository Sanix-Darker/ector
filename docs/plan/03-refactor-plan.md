# Plan 03 — Refactor Plan (module split)

## Goal
Split the `core.py` god module and the mixed `triggers_fillers.py` into cohesive,
testable modules without breaking the public API.

## Target layout
```
ector/
├── __init__.py        # exports: extract, extract_sync, __version__
├── __main__.py        # python -m ector -> cli.main()
├── api.py             # extract_sync + async extract (orchestration only)
├── types.py           # Product / Budget / ExtractResult TypedDicts, aliases
├── text_utils.py      # normalize_text, clean_phrase
├── money.py           # parse_price, is_currency_only, CURRENCY_MAP usage
├── models.py          # get_model (lru_cache), clear_model_cache, download policy
├── languages.py       # LanguageConfig + registry + get_language
├── triggers.py        # contains_trigger (word-boundary)
├── products.py        # find_main_product_tokens, collect_product_phrase, quantity
├── budget.py          # is_budget, budget assembly
├── cli.py             # argparse CLI
└── dictionary/
    ├── __init__.py    # back-compat re-exports + builders (_normalize/_validate)
    ├── currencies.py  # CURRENCY_MAP, MONEY_PATTERN, CURRENCY_ONLY_PATTERN
    ├── en.py          # REQUEST_TRIGGERS_EN, FILLER_PHRASES_EN, EN_BUDGET_HINTS
    └── fr.py          # REQUEST_TRIGGERS_FR, FILLER_PHRASES_FR, FR_BUDGET_HINTS
```

## Responsibility mapping (old → new)
| Old (core.py / triggers_fillers.py) | New |
|---|---|
| `replace_punctuation_with_fullstop` | `text_utils.normalize_text` (rewritten, BUG-014) |
| `clean_phrase` | `text_utils.clean_phrase` (rewritten, BUG-012) |
| `contains_request_triggers` | `triggers.contains_trigger` (BUG-009) |
| `find_main_product_tokens` | `products.find_main_product_tokens` (sync, RISK-005, BUG-011) |
| `collect_product_phrase` | `products.collect_product_phrase` (sync) |
| `extract_price_info` | `money.parse_price` (BUG-010, single source) |
| `extract_price_info_from_sentence` | removed (BUG-003) |
| `parse_money_entity` (triggers_fillers) | removed (BUG-002, BUG-003) |
| `maybe_budget` | `budget.is_budget` (BUG-001) |
| `add_product` | inlined in `api`/`products` helper (RISK-009 full-match) |
| `load_spacy_model` / `ensure_model_installed` | `models.get_model` (BUG-005, BUG-006) |
| `get_triggers_and_fillers` | `languages.get_language` |
| dictionaries | `dictionary/` package (BUG-004, BUG-013) |

## Async strategy
- `extract_sync` does the real work synchronously (no fake async; SMELL-001).
- `async def extract(...)` simply returns `extract_sync(...)`; cheap and keeps
  `asyncio.run(extract(...))` callers (README, tests) working unchanged.

## Backward-compat shims
- `ector/dictionary/__init__.py` re-exports all names the old `dictionary.py`
  exposed, so any code (and the diagnostics script) importing
  `from ector.dictionary import MONEY_PATTERN` keeps working.
- During refactor, `core.py`/`triggers_fillers.py` can temporarily import from new
  modules; removed in STEP 12 once nothing references them.

## Safety
- No step changes externally observable behavior until STEP 13 (the intended
  fixes), and each such change is paired with a test.
- The existing `tests/test_extract.py` is the contract that guards the refactor.
