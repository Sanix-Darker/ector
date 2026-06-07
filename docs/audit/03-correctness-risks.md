# Audit 03 — Correctness Risks (Heuristic Accuracy)

ECTOR is heuristic. This file enumerates where the heuristics are likely to be
wrong, so tests can pin behavior and future work can improve accuracy.

## RISK-001 — Quantity vs. price confusion
"I want 2 phones" → `2` parsed as price (BUG-010). Numbers without a currency and
in a quantity position should not become prices.
**Mitigation:** require currency adjacency for price, or detect `nummod`
dependency (number modifying the product noun = quantity).

## RISK-002 — Price attribution to the wrong product
A sentence with multiple products and one price (e.g. "a keyboard for 40 usd and
a monitor") assigns the same price to *both* products. Often the price belongs to
the nearest/last product or the pair.
**Decision (active, v1):** a single price in a multi-product sentence attaches to
all products in that sentence. This is intentional and tested
(`tests/test_regressions.py`); refining attribution is future work.

## RISK-003 — Multiple prices per sentence
"500 usd or 600 eur" → only the first is captured (test
`test_multiple_prices_in_one_sentence` codifies "first match"). This is a
deliberate simplification; keep it but document it.

## RISK-004 — Budget vs. price ambiguity
"a camera for 500 usd" (price) vs. "my budget is 500 usd" (budget). Relies on
budget-hint phrases + the literal word "budget". Edge cases:
- "I can spend up to 500 on a camera" — has both product and budget hint.
- Current code: if `maybe_budget` AND price → treated as budget and the sentence
  is `continue`d, so the product in the *same* sentence is dropped.
**Mitigation:** document precedence; consider extracting both product and budget
from one sentence when both are clearly present.

## RISK-005 — Existential/attr detection is English-centric
`find_main_product_tokens` checks lemmas `be`/`être`, expletives `there`/`il`.
French dependency labels differ (`fr_core_news_sm` uses different schemes). The
`attr`/`expl` branch likely never fires for French.
**Mitigation:** validate against real fr parses; adjust per-language.

## RISK-006 — `collect_product_phrase` may include irrelevant modifiers
It greedily collects all descendants except conj/cc/punct/other-main-tokens. This
can pull in prepositional phrases like "with a high-resolution screen" into the
product phrase. Sometimes desirable (descriptive), sometimes noisy.
**Mitigation:** document; optionally cap to ADJ/compound modifiers.

## RISK-007 — Currency-less budget discarded (see BUG-008)
"my budget is 300" → no budget emitted. This is a correctness gap if we decide
currency-less budgets are valid (consistency with products).

## RISK-008 — Punctuation normalization changes meaning (see BUG-014)
French elisions ("j'ai") and decimals can be mangled, changing parses.

## RISK-009 — `CURRENCY_ONLY_PATTERN` guard can drop valid products
`add_product` skips a product if `CURRENCY_ONLY_PATTERN.search(product_name)`
matches *anywhere*. A product literally named with a currency token (rare) or a
phrase containing "yen"/"pound" as a word (e.g. "pound cake", "Korean won doll")
could be wrongly dropped. `pound` matches → "pound cake" skipped.
**Mitigation:** anchor the guard to *only-currency* names (full match), not a
substring search.

## RISK-010 — Sentence segmentation depends on mangled text
Because all punctuation becomes `.`, sentence boundaries are created by the
normalizer, not the language model. This is fragile across languages.
**Mitigation:** rely on the spaCy sentencizer/parser for segmentation.

## Accuracy testing approach
See `testing/02-test-matrix.md`. We pin current *intended* behavior with tests,
fix the genuine bugs, and add regression tests for each RISK above with the
documented expected output.
