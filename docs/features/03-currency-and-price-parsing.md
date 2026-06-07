# Feature 03 — Currency & Price Parsing

## Purpose
Parse a numeric amount and a normalized currency code from text.

## Current behavior (as found)
- Two competing implementations:
  - `core.extract_price_info` (the live path): `MONEY_PATTERN.search`, returns
    `(float, currency|None)`. Currency suffix optional → bare numbers parse.
  - `triggers_fillers.parse_money_entity` (dead path): `PRICE_PATTERN.search`,
    returns `(str, currency|None)` — string price (BUG-002), never used.
- `CURRENCY_MAP` normalizes tokens/symbols to codes.
- `CURRENCY_ONLY_PATTERN` used to skip currency-only product names (substring →
  RISK-009).

## Confirmed problems
- BUG-002: string price from `parse_money_entity`.
- BUG-003: dead, divergent parser.
- BUG-010: optional currency + first-match → bare numbers/quantities become
  prices ("2 phones" → 2.0).
- RISK-003: only first price captured per sentence (intended simplification).

## Target behavior (single source of truth: `money.py`)
- One function `parse_price(text) -> (price: float|None, currency: str|None)`.
- **Currency normalization** via a single `CURRENCY_MAP`; symbols `$ € £`
  supported on either side of the number (`$25`, `25$`, `25 usd`).
- **Bare-number policy:** a number with **no** adjacent currency is *not* treated
  as a price by default, to avoid quantity/price confusion. Exception: budget
  contexts may accept a bare number as a budget amount when a budget hint is
  present (consistent with D-02-1). This resolves BUG-010 while preserving the
  existing test `test_product_with_partial_currency` ("I want a phone for 250")
  which expects a price of 250.0.
  - To preserve that test: a number is a price when it is the object of a price
    preposition ("for 250") OR has an adjacent currency. A leading `nummod` on
    the product noun ("2 phones") is a quantity, not a price.
- **Currency code set:** usd, eur, gbp, cad, aud, inr, jpy, chf, krw, sar, aed.
- `CURRENCY_ONLY_PATTERN` membership test must be a **full match** of the trimmed
  product name, not a substring (fixes RISK-009 "pound cake").

## Regex design notes
- Keep amount regex anchored to digit groups with optional decimals: `\d+(\.\d+)?`.
- Currency group references the same alternation as `CURRENCY_MAP` keys + symbols.
- Compile once at module load.

## Decisions (normative)
- D-03-1: One money parser in `money.py`; remove the dead duplicate.
- D-03-2: Bare numbers are prices only via price-preposition or currency
  adjacency; otherwise treated as quantity/ignored.
- D-03-3: First currency-qualified amount per sentence wins (keep RISK-003).

## Acceptance criteria
- "It's 25$" → (25.0, "usd"); "25 eur" → (25.0, "eur"); "500 Rupees" → (500.0, "inr").
- "I want a phone for 250" → price 250.0, currency None (existing test).
- "I want 2 phones" → no price; quantity handled per Feature 01.
