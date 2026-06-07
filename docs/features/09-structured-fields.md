# Feature 09 — Structured E-commerce Fields

ECTOR is positioned as a fast, deterministic **e-commerce request parser**: it
turns a free-form shopping sentence into a structured query, as a local
alternative to calling an LLM. Beyond products + budget, it extracts the fields
shoppers actually express.

## Output schema (current, all additive / backward compatible)

```jsonc
{
  "products": [
    {
      "product": "Red nike shoes",   // cleaned name (always present)
      "price": 200.0,                  // optional, when tied to the product
      "currency": "usd",              // optional, lowercase code
      "quantity": 2,                   // optional, "2 phones"
      "brand": "nike",                // optional, matched brand (typo-tolerant)
      "attributes": ["red"],          // optional, colors/sizes/materials/descriptors
      "condition": "new"              // optional: new | used | refurbished
    }
  ],
  "budget": { "price": 150.0, "currency": "usd" },        // optional
  "price_constraint": {                                      // optional
    "type": "max",                    // max | min | around | between
    "value": 200.0,                    // for max/min/around
    "min": 100.0, "max": 200.0,        // for between
    "currency": "usd"
  },
  "intent": "buy"                      // buy | price_check | availability | compare | browse
}
```

Existing keys (`products`, `product`, `price`, `currency`, `budget`, `quantity`)
are unchanged. New keys appear only when detected, except `intent` which is
always present (a coarse, always-useful signal).

## Field detection

### brand (`ector/attributes.py::detect_brand`)
Fuzzy-matches tokens in the product phrase against the brand catalog
(`dictionary/catalog.py::BRANDS`). Typo-tolerant ("adidss" -> "adidas").

### attributes (`detect_attributes`)
Colors, sizes, storage units, materials, and quality descriptors from
`dictionary/attributes.py`, canonicalised and de-duplicated, typo-tolerant.

### condition (`detect_condition`)
Maps phrases to `new` | `used` | `refurbished` (en/fr), multi-word phrases first
("brand new", "second hand", "remis à neuf").

### price_constraint (`ector/constraints.py::parse_constraint`)
Regex-driven, en/fr:
- max: under / below / less than / no more than / up to / at most / max / "200 max"
  / moins de / au plus / jusqu'à
- min: over / above / more than / at least / from / min / plus de / au moins / à partir de
- around: around / about / approximately / ~ / environ / autour de
- between: between X and Y / from X to Y / entre X et Y / de X à Y
Shorthand "2k" and separators handled via `money._to_float`.

### intent (`ector/intent.py::classify_intent`)
Precedence: price_check > availability > compare > buy > browse. Keyword-driven,
en/fr.

## Design notes
- All detection is pure and fast; fuzzy indexes are cached.
- Constraint/comparison/question words (under, between, much, moins, combien…)
  are excluded from product names so they never leak as products.
- These fields make ECTOR a practical NL→structured-query engine for search,
  filtering, and routing in e-commerce, without an LLM call.

## Future field ideas (not yet implemented)
- `category` (electronics, fashion…) via a category map over the catalog.
- `sort`/preference (cheapest, newest, best-rated).
- multiple budgets / per-product price constraints.
- delivery / time constraints ("by friday", "express shipping").
