# Audit 01 — Bug Catalog

Each bug has: ID, severity, location, description, root cause, reproduction, and
the intended fix. Severities: **P0** (breaks correctness/crashes), **P1** (wrong
results in common cases), **P2** (wrong results in edge cases), **P3** (cosmetic
/ doc / perf-only).

---

## BUG-001 — French budget hints never used (lang dropped) — P1

**Location:** `ector/core.py`, `extract()` calls `await maybe_budget(sentence_text)`
(twice) without passing `lang`.

**Description:** `maybe_budget(sentence_text, lang="en")` defaults to English. In
`extract()` the calls omit `lang`, so when processing French input, the function
checks `EN_BUDGET_HINTS` instead of `FR_BUDGET_HINTS`. French budget phrases like
"je n'ai que 15 eur" are not recognized as budgets.

**Root cause:** Missing argument propagation.

**Reproduction:**
```python
asyncio.run(extract("je n'ai qu'un budget de 300 dollars", "fr"))
# "budget" substring saves this case, but "je n'ai que 50 euros" (no word
# 'budget') would NOT be detected as a budget in French.
```

**Fix:** Thread `lang` through to `maybe_budget`.

---

## BUG-002 — `parse_money_entity` returns price as `str`, not `float` — P1

**Location:** `ector/triggers_fillers.py::parse_money_entity` returns
`match.group(1)` (a string) as the price.

**Description:** Inconsistent with `extract_price_info`, which returns
`float(amount_str)`. Any consumer of `parse_money_entity` gets a string price,
breaking numeric comparisons (`price > 0`) and JSON expectations.

**Root cause:** Missing `float()` cast.

**Note:** Currently masked because `extract()` never calls this path (see BUG-003).

**Fix:** Cast to float, and unify with the single money parser in target design.

---

## BUG-003 — Dead code: `extract_price_info_from_sentence` / `parse_money_entity` — P2

**Location:** `ector/core.py::extract_price_info_from_sentence` and
`ector/triggers_fillers.py::parse_money_entity`.

**Description:** Neither is called anywhere in the runtime path. `extract()` uses
`extract_price_info` (regex on raw text) and never inspects spaCy `MONEY`
entities. This is dead, divergent logic that will rot.

**Root cause:** Refactor left two competing money parsers; one was abandoned.

**Fix:** Remove dead code; consolidate into `money.py`. Decide whether MONEY
entities are useful as a secondary signal (documented in
`features/03-currency-and-price-parsing.md`).

---

## BUG-004 — Missing commas cause silent string concatenation in dictionaries — P1

**Location:** `ector/dictionary.py`:
- `FILLER_PHRASES_EN`: the entry
  `"it would be nice to buy a", "...buy an", "it would be nice to buy some"`
  is followed (no comma) by `"some"`, producing
  `"it would be nice to buy somesome"`.
- `FILLER_PHRASES_FR`: `"...j'ai la volonté d'acheter des"` is followed (no comma)
  by `"je cherche"`, producing `"j'ai la volonté d'acheter desje cherche"`.

**Description:** Python implicitly concatenates adjacent string literals. A
missing comma silently merges two list entries into one nonsensical phrase, and
drops a phrase that was meant to exist.

**Root cause:** Hand-maintained huge literal lists; easy to miss a comma.

**Reproduction:**
```python
from ector.dictionary import FILLER_PHRASES_EN
assert "it would be nice to buy somesome" in FILLER_PHRASES_EN  # True (bug)
assert "some" in FILLER_PHRASES_EN  # this exact 'some' standalone is missing
```

**Fix:** Repair the comma; add a test that asserts no filler/trigger entry
contains a doubled token or suspicious concatenation, and that lists are unique.

---

## BUG-005 — spaCy model reloaded on every `extract()` call — P1 (performance)

**Location:** `ector/triggers_fillers.py::load_spacy_model` → `spacy.load(...)`
invoked from `extract()` each call.

**Description:** `spacy.load` parses and deserializes the whole model from disk
(hundreds of ms). Calling `extract()` in a loop reloads it every time, making the
library effectively unusable at any volume.

**Root cause:** No memoization.

**Fix:** Cache loaded models per language (`functools.lru_cache`), and only load
the pipeline components actually needed.

---

## BUG-006 — `ensure_model_installed` shells out to `python` — P2

**Location:** `ector/triggers_fillers.py::ensure_model_installed` runs
`subprocess.run(["python", "-m", "spacy", "download", model_name])`.

**Description:** On many systems (incl. this macOS box) `python` does not exist;
only `python3`. Using the bare `python` name can hit the wrong interpreter or
fail. Also, downloading at first-use is a surprising runtime side effect (network
+ subprocess) hidden inside a "load" call.

**Root cause:** Hardcoded interpreter name; download-on-demand design.

**Fix:** Use `sys.executable` instead of `"python"`. Make auto-download opt-in
and clearly documented; raise a helpful error if the model is missing and
auto-download is disabled.

---

## BUG-007 — README/docstring schema mismatch: `product_requests` vs `products` — P3

**Location:** `ector/core.py::extract` docstring documents a `product_requests`
key. The function returns `products`. README correctly uses `products`.

**Root cause:** Docstring not updated after rename.

**Fix:** Correct the docstring to match the actual (and README) schema.

---

## BUG-008 — Budget dropped when currency is unknown, but product prices are not — P2

**Location:** `ector/core.py::extract` final assembly:
```python
if budget_info["price"] and budget_info["price"] > 0 and budget_info["currency"]:
    return {"products": products, "budget": budget_info}
```

**Description:** A budget with a valid positive price but no detected currency is
silently discarded. Yet for products, a price without currency is kept. This is
inconsistent. e.g. "my budget is 300" yields no budget at all.

**Root cause:** Over-strict guard requiring currency for budget only.

**Fix:** Decide a consistent policy (documented in
`features/02-budget-detection.md`): keep budget when price > 0 even if currency
is unknown, mirroring product behavior. Update tests accordingly.

---

## BUG-009 — Substring trigger matching causes false positives — P2

**Location:** `ector/core.py::contains_request_triggers` uses
`trigger in low_text`. Triggers include very short words like `"some"`, `"have"`,
`"want"`, `"get"`, `"buy"`, `"need"`.

**Description:** Naive substring matching matches inside larger words:
- `"some"` matches "awe**some**", "**some**thing".
- `"have"` matches "be**have**".
- `"get"` matches "for**get**", "to**get**her", "bud**get**".

`"get"`/`"have"` inside "budget" / unrelated words can mis-trigger product
extraction.

**Root cause:** Plain substring containment without word boundaries.

**Fix:** Match on token/word boundaries (regex `\b` or token-set lookup against
the spaCy doc), not raw substrings.

---

## BUG-010 — `MONEY_PATTERN` matches bare numbers, leaking prices — P2

**Location:** `ector/dictionary.py::MONEY_PATTERN` — the currency group is
optional, and `extract_price_info` returns on the first match.

**Description:** Because the currency suffix is optional, any standalone integer
is treated as a price. In a product sentence with an incidental number (e.g.
"I want 2 phones") the `2` is parsed as the price `2.0`. Combined with `.search`
returning the *first* number, this misattributes quantities as prices.

**Root cause:** Over-eager optional-currency regex + first-match semantics.

**Fix:** Documented in `features/03-currency-and-price-parsing.md`: prefer
amounts adjacent to a currency token/symbol; treat bare leading quantities
(e.g. "2 phones") as quantity, not price. Add targeted tests.

---

## BUG-011 — `find_main_product_tokens` docstring example is invalid — P3

**Location:** `ector/core.py::find_main_product_tokens` docstring:
```python
>>> product_tokens = find_main_product_tokens(doc.sents[0])
```

**Description:** `doc.sents` is a generator, not indexable (`doc.sents[0]`
raises `TypeError`). Also the function is `async`, so the example would need
`await`. The example is wrong and misleads users/doctest.

**Fix:** Correct the example (`next(doc.sents)` + await/asyncio) or convert the
function to sync per the refactor.

---

## BUG-012 — `clean_phrase` filler removal is single-pass and order-fragile — P2

**Location:** `ector/core.py::clean_phrase`.

**Description:** It iterates the filler list and strips a prefix when it matches.
Because it mutates `phrase`/`lower_phrase` mid-loop and continues iterating the
remaining fillers, the result depends on filler ordering, and only the
first-matching filler in list order is removed. Overlapping fillers
("i want" vs "i want a") interact unpredictably. Note also that product phrases
built by `collect_product_phrase` start at the product NOUN, so leading fillers
(which are verbs/pronouns) are usually already excluded — meaning the filler list
is largely ineffective in practice and needs reevaluation.

**Fix:** Replace with a deterministic longest-match-first strip of a leading
filler, then a single article strip; add tests. Reassess whether the giant
filler lists are needed at all given phrase construction starts at the noun.

---

## BUG-013 — Duplicate / contradictory entries in trigger & filler lists — P3

**Location:** `ector/dictionary.py` — `REQUEST_TRIGGERS_*` and `FILLER_PHRASES_*`
contain many duplicates (the lists are re-appended with overlapping content), and
`FILLER_PHRASES_*` even include trigger-like phrases.

**Description:** Duplicates waste cycles (linear scans) and make maintenance
error-prone. There is no dedupe, no validation, no normalization step.

**Fix:** Deduplicate at load, store as `frozenset` where membership is all that
matters, keep ordered lists only where longest-match ordering is required, and
add a validation test.

---

## BUG-014 — `replace_punctuation_with_fullstop` destroys contractions/decimals — P2

**Location:** `ector/core.py::replace_punctuation_with_fullstop`.

**Description:** It replaces *every* punctuation char with `.`. This turns
`it's` into `it.s`, `9.99` into `9.99` (dot is punctuation → stays `.` so okay),
but `e.g. 1,000` and apostrophes in French (`j'ai` → `j.ai`) get mangled, which
can change tokenization, lemmas, and trigger/filler matching. Replacing `'`
breaks French elision handling that the fr model relies on.

**Root cause:** Blunt normalization intended to split run-on sentences, applied
to all punctuation.

**Fix:** Only normalize sentence-ending/segmenting punctuation needed for
sentence segmentation; do not destroy apostrophes/decimal separators. Prefer
relying on spaCy's sentence segmenter. Documented in
`features/01-product-extraction.md`.

---

## BUG-015 — Language models not declared as dependencies — P2

**Location:** `pyproject.toml` dependencies list only `spacy`.

**Description:** `en_core_web_sm` / `fr_core_news_sm` are required at runtime but
not installable via normal dependency resolution. The code papers over this with
a runtime `spacy download` subprocess (see BUG-006), which fails offline / in
restricted CI.

**Fix:** Declare models as extras / direct URL dependencies, and document
installation. Update CI to install them explicitly.

---

## BUG-016 — CI mutates `pyproject.toml` and lacks models — P3

**Location:** `.github/workflows/ci.yml` runs `poetry add ruff` / `poetry add
pytest` (already dev deps) and never downloads spaCy models, so `pytest` would
fail to load models (or trigger a runtime download).

**Fix:** Remove redundant `poetry add`; install models explicitly in CI; cache
them.

---

## Summary table

| ID | Sev | One-liner |
|----|-----|-----------|
| BUG-001 | P1 | `maybe_budget` called without `lang` → FR budget hints unused |
| BUG-002 | P1 | `parse_money_entity` returns price as str |
| BUG-003 | P2 | Dead, divergent money-parsing code |
| BUG-004 | P1 | Missing commas → concatenated filler entries |
| BUG-005 | P1 | Model reloaded every call (no cache) |
| BUG-006 | P2 | `ensure_model_installed` uses `python`, not `sys.executable` |
| BUG-007 | P3 | Docstring says `product_requests`, code returns `products` |
| BUG-008 | P2 | Budget dropped when currency unknown (inconsistent) |
| BUG-009 | P2 | Substring trigger matching → false positives |
| BUG-010 | P2 | Optional-currency regex parses bare numbers as price |
| BUG-011 | P3 | Invalid docstring example (`doc.sents[0]`) |
| BUG-012 | P2 | `clean_phrase` order-fragile filler removal |
| BUG-013 | P3 | Duplicate/contradictory dictionary entries |
| BUG-014 | P2 | Punctuation normalization mangles apostrophes/decimals |
| BUG-015 | P2 | spaCy models not declared as deps |
| BUG-016 | P3 | CI mutates pyproject, lacks model install |
