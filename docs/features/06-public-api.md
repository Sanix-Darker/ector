# Feature 06 — Public API

## Purpose
Define and stabilize the public surface of ECTOR.

## Current surface
```python
from ector import extract           # async def extract(text, lang="en") -> dict
```

## Target surface (backward compatible)
```python
from ector import extract           # awaitable, returns dict (unchanged shape)
from ector import __version__       # version string
# Optional additions (additive, non-breaking):
from ector import extract_sync      # synchronous variant
```

### `extract`
- Signature: `async def extract(text: str, lang: str = "en") -> ExtractResult`.
- Remains awaitable so existing `asyncio.run(extract(...))` callers and tests
  keep working.
- Internally delegates to a synchronous implementation (no fake async).

### `extract_sync` (new, additive)
- `def extract_sync(text: str, lang: str = "en") -> ExtractResult`.
- The real implementation; `extract` wraps it.

### Result typing (`types.py`)
```python
class Product(TypedDict, total=False):
    product: str        # required in practice
    price: float
    currency: str
    quantity: int       # additive (Feature 01 open question)

class Budget(TypedDict, total=False):
    price: float
    currency: str

class ExtractResult(TypedDict, total=False):
    products: list[Product]   # always present
    budget: Budget            # present only when inferred
```

## Backward-compatibility guarantees
- `from ector import extract` keeps working.
- `await extract(text)` keeps working and returns `{"products": [...]}` and
  optional `"budget"`.
- Output dict keys unchanged: `products`, `product`, `price`, `currency`,
  `budget`.

## Decisions (normative)
- D-06-1: `extract` stays async for compatibility; `extract_sync` added.
- D-06-2: Typed results via `TypedDict` (runtime remains plain dicts).
