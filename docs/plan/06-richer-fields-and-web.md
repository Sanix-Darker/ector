# Plan 06 — Richer Fields, Performance, and Web Showcase

Three workstreams. Each chunk has a verification gate.

## Positioning
ECTOR = a fast, deterministic **e-commerce request parser** (NL -> structured
shopping query). A local alternative to calling an LLM for query understanding:
no network, no token cost, millisecond latency, reproducible output.

## Workstream 1 — Richer structured fields (new features)
Augment the result schema with OPTIONAL fields (backward compatible: existing
keys unchanged; new keys only appear when detected).

Per product:
- `brand`: matched against the brand catalog (e.g. "iphone" -> brand "apple"?
  No: keep the surface brand token, e.g. "nike"). Tagged when a catalog brand
  appears in the phrase.
- `attributes`: list of recognised descriptors (colors, sizes, storage, common
  adjectives like "wireless", "waterproof").
- `condition`: one of new | used | refurbished (en/fr synonyms).
- `quantity`: already present.

Per result (top-level):
- `budget`: already present.
- `price_constraint`: {type: max|min|around|between, value/min/max, currency}
  parsed from "under 200", "less than", "around 50", "between 100 and 200",
  "200 max", "à partir de", "moins de", "entre X et Y".
- `intent`: buy | price_check | availability | compare | browse (from triggers).

Chunks:
- 1A `dictionary/attributes.py`: colors, sizes, storage units, materials,
  conditions (en/fr).
- 1B `ector/attributes.py`: detect attributes + condition in a product phrase.
- 1C `ector/constraints.py`: parse price constraints (max/min/around/between).
- 1D `ector/intent.py`: classify intent from trigger/keywords.
- 1E wire into `api.py`; extend `types.py`; all additive + tested.

## Workstream 2 — Performance, stability, reliability
- 2A Micro-bench harness `scripts/bench.py`: cases/sec, p50/p95 latency.
- 2B Optimize: disable unused spaCy pipes where safe, use `nlp.pipe` batch path
  internally, precompute language structures, cache fuzzy lookups, avoid repeated
  lowercasing. Target: > a few thousand short queries/sec after warmup on this
  machine; single call p50 < 1ms (excluding first model load).
- 2C Robustness: never raise on arbitrary input; fuzz with random unicode/empty/
  huge strings; add a property-style test.
- 2D Determinism: same input -> same output (already; add a guard test).

## Workstream 3 — Web showcase (separate runnable, not a hard dep)
A FastAPI app exposing ECTOR + a static single-page UI.
- 3A `web/app.py`: FastAPI with `POST /api/extract` {text, lang} -> result; also
  serve static UI. ECTOR stays import-only; FastAPI/uvicorn are an optional
  `web` extra so the core library has no web deps.
- 3B `web/static/index.html` + CSS/JS: left = big textarea, right = JSON view,
  language selector, "Compute" button, clickable placeholder examples, a
  `pip install ector` command banner with copy button. Clean, light, shadcn-like
  aesthetic (neutral palette, rounded cards, subtle borders) using plain
  CSS (no build step).
- 3C `web/README.md` + run docs; smoke test with FastAPI TestClient.
- 3D Optional: `GET /api/health`, `GET /api/examples`.

## Gates
- Lint clean, full unit suite green, corpus thresholds maintained or improved.
- Bench numbers recorded in `docs/plan/07-status-2.md`.
- Web smoke test passes via TestClient (no network).
