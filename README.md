## ECTOR

A fast, deterministic **e-commerce request parser**: it turns a free-form,
natural-language shopping request into a structured query (products, prices,
currencies, budget, price constraints, brand, attributes, condition, intent).

Think of it as a local, millisecond, zero-cost alternative to calling an LLM for
shopping-query understanding.

### DISCLAIMER

This is not an "OpenAI wrapper". It uses classic NLP (Natural Language
Processing) via [spaCy](https://spacy.io/) — part-of-speech tagging and
dependency parsing — combined with curated dictionaries, a fuzzy-matching layer
for typo tolerance, regular expressions for money parsing, and a parse-independent
token fallback. The result is deterministic and offline.

### HIGHLIGHTS

- **Typo-tolerant**: handles messy input ("i wnat an ipone and a chargr, budjet
  200 euoros") via fuzzy normalization of known vocabulary (currencies, brands,
  products, triggers) and a parse-independent fallback extractor.
- **Rich structured output**: products with `price`, `currency`, `quantity`,
  `brand`, `attributes`, `condition`; plus top-level `budget`, `price_constraint`
  (max/min/around/between), and `intent`.
- **Fast**: ~2 ms per request after warmup (the spaCy model is cached; unused
  pipeline components are disabled).
- **Bilingual**: English and French.
- **Robust**: never raises on arbitrary input; deterministic output.

### REQUIREMENTS

- Python `>=3.10,<3.13`
- [spaCy](https://pypi.org/project/spacy/) `>=3.8,<4`
- spaCy language models: `en_core_web_sm` (English), `fr_core_news_sm` (French)

### HOW TO INSTALL

```bash
pip install ector

# Language models are required at runtime. Install them either via the extra:
pip install "ector[models]"

# ...or directly with spaCy:
python -m spacy download en_core_web_sm
python -m spacy download fr_core_news_sm
```

> If a model is missing at runtime, ECTOR raises a clear error telling you which
> `spacy download` command to run. You can also set `ECTOR_AUTO_DOWNLOAD=1` to
> let ECTOR download a missing model automatically (uses the current Python
> interpreter).

### HOW TO USE (Python)

```python
import json
import asyncio
from ector import extract

text = (
    "Hello, do you have some apple juice at 9 eur? "
    "i also want bananas, but i only have 15 eur"
)
print(json.dumps(asyncio.run(extract(text)), indent=2))
```

```json
{
  "products": [
    { "product": "Apple juice", "price": 9.0, "currency": "eur" },
    { "product": "Bananas" }
  ],
  "budget": { "price": 15.0, "currency": "eur" },
  "intent": "buy"
}
```

A synchronous variant is also available:

```python
from ector import extract_sync

result = extract_sync("I want a refurbished macbook under 1200 usd", "en")
# {
#   "products": [{"product": "Refurbished macbook", "brand": "macbook",
#                 "condition": "refurbished"}],
#   "price_constraint": {"type": "max", "value": 1200.0, "currency": "usd"},
#   "intent": "buy"
# }
```

French is supported via `lang="fr"`:

```python
extract_sync("je veux un iPhone noir, mais j'ai un budget de 300 dollars", "fr")
```

### WEB SHOWCASE

A FastAPI demo with a clean single-page UI (left: request textarea, right: live
JSON) lives in [`web/`](./web). The core library has no web dependencies.

```bash
pip install -e ".[web,models]"
uvicorn web.app:app --reload
# open http://127.0.0.1:8000
```

### HOW TO USE (CLI)

```bash
# positional text
ector "I want a laptop for 150 usd, my budget is 200 eur"

# French
ector --lang fr "je veux un iPhone, budget 300 dollars"

# from a file or STDIN
ector --file input.txt
echo "I need a wireless mouse" | ector --compact

# also available as a module
python -m ector "I want a green phone"
```

### OUTPUT SCHEMA

```jsonc
{
  "products": [
    {
      "product": "string",   // cleaned product name (always present)
      "price": 0.0,           // optional, present when tied to the product
      "currency": "usd",      // optional, lowercase code when known
      "quantity": 1,           // optional, when a quantity like "2 phones" is found
      "brand": "nike",        // optional, recognised brand (typo-tolerant)
      "attributes": ["red"],  // optional, colors/sizes/materials/descriptors
      "condition": "new"      // optional: new | used | refurbished
    }
  ],
  "budget": {                  // optional, present only when inferred
    "price": 0.0,
    "currency": "usd"          // optional
  },
  "price_constraint": {        // optional: under/over/around/between
    "type": "max",            // max | min | around | between
    "value": 200.0,            // for max/min/around
    "min": 100.0, "max": 200.0, // for between
    "currency": "usd"
  },
  "intent": "buy"              // buy | price_check | availability | compare | browse
}
```

See [`docs/features/09-structured-fields.md`](./docs/features/09-structured-fields.md)
for full field semantics.

### DOCUMENTATION

Full planning, audit, feature specs, and testing docs live in [`docs/`](./docs).
Start with [`docs/README.md`](./docs/README.md).

### DEVELOPMENT

```bash
# create an environment (Python 3.10-3.12) and install
pip install -e ".[models]"
pip install pytest ruff

# lint and test
ruff check .
pytest

# benchmark and measure extraction quality on the 12k-case corpus
python scripts/bench.py
python scripts/measure.py
```

### AUTHOR

- Sanix-Darker
