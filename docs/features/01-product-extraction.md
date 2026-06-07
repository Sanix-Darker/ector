# Feature 01 — Product Extraction

## Purpose
Identify the products a user wants and produce a clean product name, optionally
with an attached price and currency.

## Current behavior (as found)
1. Text is normalized by replacing every punctuation char with `.` (problematic —
   see BUG-014).
2. Per sentence, candidate product tokens are found via dependency parsing
   (`find_main_product_tokens`): `dobj`/`obj`, certain `pobj`, existential
   `attr`, plus conjuncts.
3. For each product token, `collect_product_phrase` gathers the token and its
   descendants (minus conj/cc/punct/other product tokens).
4. `clean_phrase` strips a leading filler phrase, then a leading article, trims
   punctuation, capitalizes.
5. `add_product` drops currency-only names and attaches price/currency.

## Confirmed problems
- BUG-014: apostrophes/decimals mangled by punctuation normalization.
- BUG-012: filler stripping is order-fragile and largely ineffective because the
  phrase already starts at the product noun.
- RISK-006: greedy descendant collection can pull in prepositional phrases.
- RISK-009: `add_product`'s `CURRENCY_ONLY_PATTERN.search` drops "pound cake".
- BUG-010: bare numbers become prices, so "2 phones" → product "2 phones",
  price 2.0.

## Target behavior
- **Normalization:** stop destroying apostrophes and decimals. Only segment on
  real sentence terminators; otherwise defer to spaCy. French elision must be
  preserved so `fr_core_news_sm` tokenizes correctly.
- **Product token discovery:** keep the dependency-based approach, but make
  language assumptions explicit. Add quantity handling: a leading `nummod`
  attached to the product noun is a quantity, not a price, and should be excluded
  from the product *name* (or retained as a separate `quantity` field — see Open
  Questions).
- **Phrase cleaning:** deterministic longest-filler-first strip; single article
  strip; trim punctuation; capitalize. Guard against empty results.
- **Currency-only guard:** only skip a product if its *entire* name is a currency
  token (full-match), never a substring; "pound cake" must survive.

## Output examples (target)
```
"I'm looking for a new laptop."        -> {product: "New laptop"}
"I want a smartphone for 200 USD."     -> {product: "Smartphone", price: 200.0, currency: "usd"}
"I want a pound cake."                 -> {product: "Pound cake"}
"I want 2 phones."                     -> {product: "Phones", quantity: 2}   (target; see Open Qs)
```

## Open questions
- **Quantity:** expose a `quantity` field, or fold into the name, or ignore? The
  safest non-breaking choice is to *exclude the bare number from the price* and
  keep it out of the name; adding a `quantity` field is an additive enhancement.
  Decision recorded in `plan/02-micro-plan.md`.

## Acceptance criteria
- All current tests pass (after intended behavioral fixes documented in
  `testing/02-test-matrix.md`).
- New regression tests for pound cake, quantity, and French elision pass.
