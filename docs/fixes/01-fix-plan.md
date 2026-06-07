# Fixes 01 — Remediation Plan

Maps every audit item to a concrete fix, the target module, and how it is
verified. Status legend: ☐ todo, ◐ in progress, ☑ done.

**All items below are ☑ done and verified by the test suite (86 tests) + lint.**

| ID | Fix summary | Target module | Verified by | Status |
|----|-------------|---------------|-------------|--------|
| BUG-001 | Pass `lang` to budget detection | `budget.py` / `api.py` | test: FR budget hint | ☑ |
| BUG-002 | Single float-returning money parser | `money.py` | test: money types | ☑ |
| BUG-003 | Remove dead `parse_money_entity` / `extract_price_info_from_sentence` | removed | grep + tests green | ☑ |
| BUG-004 | Fix missing commas; dedupe; validate | `dictionary/en.py`, `dictionary/fr.py` | test: no concatenated entries | ☑ |
| BUG-005 | `functools.cache` model loading | `models.py` | test: spy on `spacy.load` | ☑ |
| BUG-006 | `sys.executable`; opt-in download | `models.py` | test: error message + interpreter | ☑ |
| BUG-007 | Fix docstring schema → `products` | `api.py` | doctest + doc review | ☑ |
| BUG-008 | Emit budget without currency (consistent) | `budget.py` | test: "budget is 300" | ☑ |
| BUG-009 | Word-boundary trigger matching | `triggers.py`, `languages.py` | test: "forget"≠trigger | ☑ |
| BUG-010 | Bare numbers not auto-priced; quantity logic | `money.py`, `products.py` | test: "2 phones" | ☑ |
| BUG-011 | Fix/replace invalid docstring example | `products.py` | doctest passes | ☑ |
| BUG-012 | Deterministic longest-match filler strip | `text_utils.py` | test: clean_phrase | ☑ |
| BUG-013 | Dedupe + validate dictionaries | `dictionary/__init__.py` | test: uniqueness | ☑ |
| BUG-014 | Preserve apostrophes/decimals in normalize | `text_utils.py` | test: FR elision | ☑ |
| BUG-015 | Declare models as extras | `pyproject.toml` | wheel build + extras | ☑ |
| BUG-016 | Fix CI: install models, drop redundant `poetry add` | `.github/workflows/ci.yml` | workflow review | ☑ |
| RISK-009 | Full-match currency-only guard | `money.py` | test: "pound cake" | ☑ |

## Behavioral changes that may affect existing tests
- BUG-008 changes budget emission to not require currency. Existing budget tests
  all include a currency, so they still pass. New test added for the no-currency
  case.
- BUG-010 changes "I want 2 phones" from `{product:"2 phones", price:2.0}` to
  `{product:"Phones", quantity:2}` (no price). New test added. We must verify the
  existing `test_product_with_partial_currency` ("phone for 250" → price 250.0)
  still passes because that number is a price-preposition object, not a quantity.

## Fix sequencing
See `plan/02-micro-plan.md`. Order is chosen so each step keeps the suite green:
1. Introduce new modules alongside old code (no behavior change).
2. Switch `api.extract` to new modules.
3. Remove old modules.
4. Add new-behavior fixes + tests.
5. Packaging/CI/CLI.
