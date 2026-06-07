# 01 — Project Overview

## What is ECTOR?

ECTOR ("**E**xtra**C**t" + "vec**TOR**", informally) is a small Python library
that takes a free-form, natural-language text written by a shopper and extracts:

1. **Products** the user wants, each optionally with a **price** and **currency**.
2. A single overall **budget** (price + currency), when the text implies one.

It is explicitly **not** an "OpenAI/LLM wrapper". It uses classic NLP via
[spaCy](https://spacy.io/) — part-of-speech tagging, dependency parsing, and
named-entity recognition — combined with curated trigger/filler dictionaries and
regular expressions for money parsing.

## Public contract

```python
import asyncio
from ector import extract

result = asyncio.run(extract(
    "Hello, do you have some apple juice at 9 eur? "
    "I also want bananas, but I only have 15 eur",
    "en",
))
```

Expected shape:

```json
{
  "products": [
    { "product": "Apple juice", "price": 9.0, "currency": "eur" },
    { "product": "Bananas" }
  ],
  "budget": { "price": 15.0, "currency": "eur" }
}
```

### Output schema (target, normative)

- `products`: array (always present, possibly empty).
  - `product`: string (required, non-empty).
  - `price`: number (optional; present only when a positive price is tied to the product).
  - `currency`: string ISO-like lowercase code (optional; present only when known).
- `budget`: object (optional; present only when a budget is inferred).
  - `price`: number (> 0).
  - `currency`: string (lowercase code) — see open question in
    `features/02-budget-detection.md` about currency-less budgets.

## Supported languages

- English (`en`) — default.
- French (`fr`).

The architecture must keep language a first-class, easily-extensible parameter.

## Non-goals

- No remote API calls at request time (model download is the only network use,
  and should ideally be a packaging/installation concern, not runtime).
- No attempt at 100% accuracy. ECTOR is a fast heuristic extractor.
- No multi-budget support (a single budget per input).

## Runtime requirements

- Python `>=3.10,<3.13` (spaCy 3.8 constraint).
- spaCy `>=3.8,<4`.
- Language models: `en_core_web_sm`, `fr_core_news_sm`.

## Current status (as found)

The library runs but has multiple confirmed bugs, dead code, performance
problems (model reloaded per call), documentation drift (README vs. code), and
no caching/CLI/typing guarantees. See the `audit/` folder for the complete list.
