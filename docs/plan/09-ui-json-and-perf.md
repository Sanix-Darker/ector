# Plan 09 — Collapsible JSON view, perf, and project gaps (micro-plan)

Scope: a collapsible/line-numbered JSON viewer in the web app, a GitHub link,
performance optimization of the processing path, and filling investigated gaps.
Each element is specified with data flow, states, and verification.

## A. Collapsible JSON viewer (web)
Goal: multi-level expand/collapse with line numbers, in vanilla JS (no deps).

A1. Build a recursive renderer that turns the result object into a tree of DOM
    rows, each row = one "line" with: a gutter line-number, indentation, an
    optional caret (▸/▾ as SVG, not emoji) for objects/arrays, the key, and the
    value (syntax-tinted).
A2. Collapsing a node hides its child rows and shows a compact summary on the
    opening line (e.g. `{ … } 3 keys` / `[ … ] 2 items`) plus the closing
    bracket appended. Re-expanding restores children.
A3. Line numbers: a fixed-width left gutter; numbers recomputed against
    *visible* rows so they stay contiguous after collapse. (Decision: number the
    visible lines 1..N; simpler and readable.)
A4. Controls in the output pane head: "Expand all" / "Collapse all" (collapse to
    top-level children), and keep "Copy JSON" (copies full pretty JSON).
A5. Caret affordance: click caret OR the key toggles. Keyboard: row focusable,
    Enter/Space toggles. ARIA: `role="treeitem"`, `aria-expanded`.
A6. Performance: results are tiny (a handful of products); a full re-render on
    each compute is fine. Avoid layout thrash by building in a fragment.
A7. Theme: line numbers use --muted; carets use currentColor; tints use the
    existing --json-* vars.

States: empty (placeholder line), error (single muted line), normal (tree).

Verify: compute a multi-product result; collapse the root, a product object, and
the attributes array independently; line numbers stay contiguous; copy still
yields full JSON; works in light & dark.

## B. GitHub link (web)
B1. Add a GitHub icon button (inline SVG octocat-style mark) in the topbar
    actions, linking to https://github.com/Sanix-Darker/ector, target=_blank,
    rel="noopener", aria-label.
B2. Also expose repo URL via `/api/health` (add `repo` field) so the front-end
    can read it instead of hardcoding (single source of truth). Front-end sets
    the href from health; falls back to the hardcoded URL.

Verify: link present, correct href, opens new tab.

## C. Performance optimization of processing
Investigate and optimize the hot path (extract_sync). Candidate wins:
C1. spaCy: we already disable `ner`. Try also disabling components we never use.
    We use tagger (pos_), parser (dep_ + sentence boundaries), lemmatizer,
    attribute_ruler. Measure each; only disable if safe (tests + corpus hold).
C2. Avoid building the fuzzy catalog/attribute indexes repeatedly: ensure they
    are module-level/lru_cached (some are dict-cached; confirm no per-call
    rebuild).
C3. `normalize_vocabulary`: it tokenizes with a regex and fuzzy-corrects each
    token. Cache per (token, lang) already via lru_cache on `_correct_token`.
    Confirm the index build is cached and not rebuilt per call.
C4. Short-circuit: if text is empty/whitespace, return early (skip model call).
C5. Consider running the spaCy `tokenizer`+needed pipes once; we already call
    `nlp()` once per extract. The per-sentence work is light.
C6. Micro: precompile regexes (done), avoid repeated `.lower()` on the same
    string in hot loops where cheap.
C7. Add `scripts/bench.py` comparison before/after; record in status doc.

Target: keep correctness identical (corpus unchanged), improve calls/sec and/or
reduce p50.

## D. Project gaps investigated (library + app)
D1. `__init__` exports: ensure `extract`, `extract_sync`, `__version__` and the
    typed results are importable; consider exporting `supported_languages`.
D2. Public typed API: expose `ExtractResult`/`Product` types for consumers
    (already in `ector.types`; re-export from package root).
D3. CLI: add `--version` (exists) and ensure it can emit the new fields (it uses
    extract_sync, so yes). Consider a `--explain`? (defer; out of scope.)
D4. Web: add `/api/health` `repo` + `model_loaded` flags; add a small "about"
    line. Add request size guard (reject > N chars) to avoid abuse.
D5. Determinism/robustness already covered by tests; keep.
D6. Docs: update web README + features for the JSON viewer and repo link.

## E. Reload
E1. After all changes pass (ruff + pytest + corpus thresholds), restart the
    uvicorn server on port 8000 so the user can test.

## Verification gates
- `ruff check .` clean; `pytest` green (incl. corpus thresholds + web tests).
- `scripts/measure.py` metrics not regressed.
- `scripts/bench.py` recorded before/after.
- Live: server serves; JSON viewer collapses at multiple levels with line
  numbers; GitHub link works; light default theme; no emojis.
