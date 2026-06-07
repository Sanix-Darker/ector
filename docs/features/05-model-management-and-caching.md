# Feature 05 — Model Management & Caching

## Purpose
Load spaCy models efficiently and handle missing models gracefully.

## Current behavior (as found)
- `load_spacy_model(lang)` calls `spacy.load(...)` on **every** `extract()` call
  (BUG-005) — no caching.
- `ensure_model_installed` runs `subprocess.run(["python", "-m", "spacy",
  "download", model])` (BUG-006) — uses bare `python`, downloads at runtime.

## Confirmed problems
- BUG-005: catastrophic performance — reloading model per call.
- BUG-006: `python` may not exist (`python3` does); runtime network side effect
  hidden inside a load call; fails behind strict SSL/proxy (observed here:
  spaCy's downloader fails certificate verification while pip succeeds).

## Target design (`models.py`)
- `@lru_cache(maxsize=None)` keyed by model name → returns a loaded, reusable
  `Language` pipeline. First call loads; subsequent calls are instant.
- Optionally disable unused pipeline components for speed (we need tagger,
  parser, ner, attribute_ruler, lemmatizer; we can keep defaults for correctness
  initially and optimize later with measurements).
- **Missing model policy:**
  - Default: raise a clear, actionable error instructing the user to run
    `python -m spacy download <model>` (or install the model extra).
  - Opt-in auto-download via env var `ECTOR_AUTO_DOWNLOAD=1`, using
    `sys.executable` (not `"python"`).
- Provide `clear_model_cache()` for tests.

## Performance target
- Second and subsequent `extract()` calls must not call `spacy.load`. Verified by
  a test that patches/spies on `spacy.load` and asserts a single load per model.

## Decisions (normative)
- D-05-1: Models cached via `lru_cache`.
- D-05-2: No implicit runtime download by default; opt-in via env var using
  `sys.executable`.
- D-05-3: Models declared in packaging (extras) and installed in CI explicitly.

## Acceptance criteria
- Repeated `extract` calls reuse the cached pipeline (spy test).
- Helpful error when a model is absent and auto-download disabled.
