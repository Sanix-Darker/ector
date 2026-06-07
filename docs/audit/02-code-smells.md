# Audit 02 — Code Smells & Maintainability Issues

These are not strictly "bugs" (the code may produce correct output today) but
they harm correctness-resilience, performance, readability, and maintainability.

## SMELL-001 — Gratuitous `async` on CPU-bound, non-I/O functions
`contains_request_triggers`, `find_main_product_tokens`, `maybe_budget`,
`extract_price_info`, `add_product` are all `async` but never `await` anything
meaningful (they only `await` each other). This adds event-loop overhead and
forces callers into `asyncio.run`. **Action:** make internals synchronous; keep
only a thin async-compatible public `extract` for backward compatibility.

## SMELL-002 — One module does everything (`core.py`)
Orchestration, NLP, regex, budget, text utils, and assembly all live together.
**Action:** split per `02-architecture.md`.

## SMELL-003 — Linear scans of huge lists per sentence
`REQUEST_TRIGGERS_*` and `FILLER_PHRASES_*` have hundreds of entries scanned with
`any(substring in text)` for *every* sentence. **Action:** use sets for exact
membership; precompile a single alternation regex for trigger phrases; sort
fillers by length once for longest-match.

## SMELL-004 — Duplicated data within the same list
Trigger and filler lists were appended twice with overlapping content (and even
mix triggers into fillers). **Action:** dedupe + validate at import; add tests.

## SMELL-005 — Magic strings & repeated literals
Currency codes, language codes, dep labels, and the `"budget"` keyword are
sprinkled as raw literals. **Action:** centralize constants (`languages.py`,
`dictionary/currencies.py`).

## SMELL-006 — No type hints on returns / loose `Any`
`extract_price_info_from_sentence(...) -> tuple[Any, Any]`. **Action:** introduce
`Price = float | None`, `Currency = str | None`, and `TypedDict` results.

## SMELL-007 — Mixed concerns in `triggers_fillers.py`
It loads models *and* parses money *and* returns dictionaries. Three unrelated
responsibilities. **Action:** split into `models.py`, `money.py`, `languages.py`.

## SMELL-008 — Side-effectful import-time work risk
Dictionaries run `[t.lower() for t in ...]` at import. Fine, but combined with
the duplication it hides issues. **Action:** normalize + dedupe + validate in one
clearly named builder.

## SMELL-009 — No logging / no debuggability
There is no way to see *why* a sentence was classified as product vs. budget.
**Action:** add optional `logging` at DEBUG level in the classifier.

## SMELL-010 — `example.py` mixes languages and unrealistic inputs
Useful as a smoke test but not asserted. **Action:** keep as example; add a real
smoke test under `tests/`.

## SMELL-011 — No `[tool.ruff]` / `[tool.pytest.ini_options]` config
Linting and test discovery rely on defaults. **Action:** add explicit config to
`pyproject.toml` for reproducibility.

## SMELL-012 — `PRICE_PATTERN` in `triggers_fillers.py` duplicates `MONEY_PATTERN`
Two regexes for the same job in two files. **Action:** one money module.
