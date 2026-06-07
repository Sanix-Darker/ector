# Feature 08 — Typo Tolerance & Robust Extraction

## Goal
ECTOR must extract products, prices, currencies, and budgets from messy,
real-world e-commerce text including typos, missing/extra characters,
transpositions, keyboard-adjacent errors, spacing/casing noise, and informal
phrasing — in English and French. Target: handle 10,000+ generated edge cases
with a high pass rate.

## Why dependency parsing alone is not enough
spaCy's POS tagger and dependency parser are trained on clean text. Typos like
"lookng for a laptp" degrade tagging and parsing, so the dependency-based product
finder misses items. We therefore add two robustness layers.

## Layer 1 — Functional-vocabulary normalization (pre-spaCy)
A normalization pass corrects ONLY closed-class, controlled vocabulary to its
canonical spelling before spaCy runs. This both fixes our own detectors and
improves spaCy's parse. We never blindly "correct" open-vocabulary product names
(we cannot know them all); unknown tokens are left intact.

Corrected classes:
- **Currencies**: "dollr"→"dollar", "euoros"→"euros", "usდ"→"usd", symbols.
- **Budget keyword**: "budjet"/"budgt"→"budget".
- **High-signal trigger verbs**: "lookng"→"looking", "wnat"→"want", "ned"→"need".
- **Connectors/units**: "annd"→"and", "qty", "pcs", "x".
- **Curated common e-commerce nouns & brands** (the "giga dictionary"): correct a
  misspelled known product/brand to canonical form (e.g. "ipone"→"iphone",
  "labtop"→"laptop") so it parses and matches.

Fuzzy matching uses bounded Levenshtein distance with a length-relative
threshold, candidate bucketing by (first char, length±1), and caching for speed.

## Layer 2 — Token-based fallback extractor (parse-independent)
When the dependency-based finder yields nothing (or to augment it), a token-level
extractor:
1. Tokenizes (robust even on typos).
2. Removes functional tokens: triggers, fillers, budget phrases, currencies,
   numbers, prices, connectors, stopwords, punctuation.
3. Groups remaining contiguous content tokens into product phrases (split on
   connectors like "and"/"et"/commas).
This survives broken parses because it only needs tokenization + classification.

## Number & price robustness
- Decimal/thousand separators: "9.99", "9,99", "1,000", "1 000".
- Attached symbols/codes: "$25", "25$", "25usd", "25 usd".
- Shorthand: "1k"→1000, "2.5k"→2500.
- Spelled-out (common values), en + fr: "twenty dollars", "deux cents euros".
- Quantity vs price: leading count ("2 phones") stays a quantity (Feature 01).

## Currency robustness
- Fuzzy-normalize misspelled currency words to ISO-like codes.
- Expanded currency set + symbols + slang ("bucks"→usd, "quid"→gbp, "balles"→eur).

## Acceptance / measurement
A generator (`tests/fixtures/`) builds labelled cases from templates × catalog ×
currencies × typo profiles. A harness runs ECTOR over all cases and reports a
per-category pass rate. Assertions are typo-tolerant: a product is "captured" if
an extracted product fuzzy-matches the intended head noun; price/currency/budget
must match exactly (currency after normalization).

Target pass rates (initial): products ≥ 95%, price ≥ 97%, currency ≥ 97%,
budget ≥ 95%. We iterate on the extractor until met.

## Decisions (normative)
- D-08-1: Normalize closed-class vocabulary only; never auto-rewrite unknown
  product tokens.
- D-08-2: Token-fallback augments (not replaces) dependency extraction; union of
  results, de-duplicated by head.
- D-08-3: Fuzzy thresholds are length-relative; cached; bucketed for speed.
- D-08-4: Generated dataset is committed (deterministic seed) so CI is stable.
