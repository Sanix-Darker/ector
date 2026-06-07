# 02 — Architecture

## Current architecture (as found)

```
ector/
├── __init__.py            # exports `extract`
├── core.py                # everything: orchestration + product + price + budget + text utils
├── dictionary.py          # triggers, fillers, budget hints, currency maps, regexes
└── triggers_fillers.py    # spaCy model loading + trigger/filler accessors + money entity parse
```

### Data flow (current)

```
extract(text, lang)
  └─ replace_punctuation_with_fullstop(text)
  └─ load_spacy_model(lang)            # reloaded EVERY call (no cache)
  └─ get_triggers_and_fillers(lang)
  └─ nlp(text) -> doc
  └─ for each sentence:
        ├─ extract_price_info(text)          # regex MONEY_PATTERN
        ├─ contains_request_triggers(...)    # substring match
        ├─ find_main_product_tokens(sent)    # dependency parse
        ├─ branch: budget? product? trigger?
        └─ collect_product_phrase + clean_phrase -> add_product
  └─ assemble {products, budget?}
```

### Problems with the current architecture

1. **God module**: `core.py` mixes orchestration, NLP token logic, price regex
   parsing, budget heuristics, text normalization, and output assembly.
2. **Misleading async**: nearly every function is `async` but does no I/O. This
   adds overhead and cognitive noise without concurrency benefit.
3. **No model caching**: `load_spacy_model` calls `spacy.load` on every
   `extract()` call — extremely slow for repeated use.
4. **Dead/duplicated price logic**: `extract_price_info_from_sentence` +
   `parse_money_entity` are never used by `extract`; `extract_price_info` is the
   real path. The two disagree (one returns float, one returns str).
5. **Tight coupling to globals**: dictionaries are module-level lists scanned
   linearly per sentence.

## Target architecture

Split responsibilities into cohesive modules. Keep the public API stable
(`from ector import extract`).

```
ector/
├── __init__.py            # public API surface: extract, __version__
├── api.py                 # `extract` orchestration only (thin)
├── models.py              # spaCy model loading + caching (lru_cache)
├── languages.py           # language registry: code -> (model, triggers, fillers, hints)
├── text_utils.py          # normalization helpers (punctuation, cleaning)
├── triggers.py            # trigger detection (token/word-boundary aware)
├── products.py            # product token discovery + phrase building + cleaning
├── money.py               # price + currency parsing (single source of truth)
├── budget.py              # budget heuristics + budget assembly
├── types.py               # TypedDicts / dataclasses for results
├── dictionary/            # data only, split by concern + language
│   ├── __init__.py
│   ├── currencies.py      # CURRENCY_MAP, patterns
│   ├── en.py              # REQUEST_TRIGGERS_EN, FILLER_PHRASES_EN, EN_BUDGET_HINTS
│   └── fr.py              # REQUEST_TRIGGERS_FR, FILLER_PHRASES_FR, FR_BUDGET_HINTS
└── cli.py                 # `python -m ector` / `ector` entry point (new feature)
```

### Design principles

- **Single source of truth** for money parsing (`money.py`).
- **Deterministic & pure** functions wherever possible; isolate the only real
  side effect (model download/load) behind `models.py`.
- **Sync core, optional async wrapper**: keep `extract` awaitable for backward
  compatibility (README + tests call `asyncio.run(extract(...))`), but implement
  the heavy lifting synchronously and cleanly. See
  `plan/03-refactor-plan.md` for the compatibility approach.
- **Typed results** via `TypedDict` so editors and users get accurate hints.
- **Data vs. logic separation**: `dictionary/` holds only data; logic lives in
  the sibling modules.

### Backward compatibility constraints

- `from ector import extract` must keep working.
- `await extract(text, lang="en")` must keep working and return the documented
  schema (`products`, optional `budget`).
- Existing tests in `tests/test_extract.py` express the intended behavior and
  must continue to pass (after fixing the genuine bugs they would otherwise hide).
