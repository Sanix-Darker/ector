# Feature 02 — Budget Detection

## Purpose
Detect a single overall spending limit (budget) and emit `{price, currency}`.

## Current behavior (as found)
- `maybe_budget(text, lang="en")`: returns True if the literal word "budget" is
  present, else checks language-specific budget-hint lists.
- In `extract()`:
  - If a sentence has no triggers, no product tokens, but a price and looks like
    a budget → set budget.
  - If a sentence looks like a budget AND has a price → set budget, skip product
    extraction (`continue`).
- Final assembly only emits budget if `price > 0` **and** `currency` is set.

## Confirmed problems
- BUG-001: `maybe_budget` is called without `lang`, so French hints never apply.
  Confirmed: "je n'ai que 50 euros" (fr) yields no budget.
- BUG-008: currency-less budget is dropped. Confirmed: "My budget is 300" yields
  no budget, while products keep prices without currency — inconsistent.
- RISK-004: a sentence containing both a product and a budget hint drops the
  product (the `continue`).

## Target behavior
1. **Language correctness:** pass `lang` to `maybe_budget`. French budget hints
   must work.
2. **Currency consistency:** emit a budget whenever a positive price is detected
   in a budget context, even if currency is unknown (mirroring product price
   handling). `budget = {price: <float>}` with optional `currency`.
   - This changes one existing test expectation only where currency was required;
     verify `test_*` still align (the existing budget tests all include a
     currency, so they remain valid).
3. **Budget keyword matching** must be word-boundary aware (so "budget" matching
   is fine, but short hint fragments are not matched inside larger words).
4. **Precedence (RISK-004):** if a sentence clearly has BOTH a product (trigger +
   product token) AND a budget hint with a price, prefer extracting the product
   *and* recording the budget when they are clearly separable. Conservative v1:
   keep current precedence (budget wins, product skipped) but document it; add a
   test pinning the chosen behavior so it is intentional.

## Decisions (normative)
- D-02-1: Budget emitted when `price > 0`, regardless of currency presence.
- D-02-2: Only one budget per input; the last budget-qualifying sentence wins
  (matches current "overwrite" behavior).
- D-02-3: Budget detection is language-aware.

## Acceptance criteria
- "My budget is 300." → `{"budget": {"price": 300.0}}` (+ empty products).
- "je n'ai que 50 euros." (fr) → budget 50.0 eur.
- All existing budget tests still pass.
