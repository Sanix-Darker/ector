# Plan 08 — Web UI Enhancements (micro-plan)

Goal: add word/token counts, light/dark theme, "combine from samples", and
"random pick (any language)" to the showcase, without breaking the core library
or existing tests. Each element is specified precisely with its data flow,
states, and verification.

## Element 0 — Backend support
0.1 `POST /api/tokenize {text, lang}` → `{words, tokens, chars}`.
- words = `len(text.split())`.
- tokens = spaCy **tokenizer-only** count (no tagger/parser) of non-space tokens
  — this is the unit ECTOR reasons over; cheap.
- chars = `len(text)`.
- Unknown lang → fallback "en".
- Verify: TestClient asserts counts for a known string.
- STATUS: endpoint added.

0.2 `/api/examples` already returns `{label, lang, text}` list. No change.

## Element 1 — Word / token / char counter (bottom-left of textarea)
1.1 Footer row under the textarea: left = counts, right = existing latency.
1.2 Live local word count on every `input` event (instant, no network):
    `text.trim() ? text.trim().split(/\s+/).length : 0`.
1.3 Token count: debounced (250 ms) call to `/api/tokenize` with current text +
    lang; show `…` while pending; show last value otherwise. Avoid spamming:
    cancel/ignore stale responses via a request id.
1.4 Display format: `42 words · 51 tokens · 263 chars`.
1.5 Empty text → `0 words · 0 tokens · 0 chars`.
- Verify: type text, counts update; clearing resets to 0; backend test for
  endpoint.

## Element 2 — Light / Dark theme
2.1 CSS: move palette into `:root` (light) and `[data-theme="dark"]` overrides.
    All colors via variables already; add dark values (bg, card, border, fg,
    muted, accents, json token tints).
2.2 Toggle button in the topbar (sun/moon glyph). Click flips
    `document.documentElement.dataset.theme`.
2.3 Persistence: `localStorage["ector-theme"]`. On load: stored value, else
    `prefers-color-scheme`.
2.4 Smooth transition on bg/fg/border (150 ms) — but not on the JSON area to
    avoid flicker.
- Verify: toggle changes theme; reload keeps it; system preference respected
  when unset.

## Element 3 — "Combine from samples"
3.1 Button near examples. On click: pick 2 distinct samples **of the same
    language** (so the combined sentence is monolingual and meaningful), join
    their texts into one request, set lang, fill textarea, auto-compute.
3.2 Joining: concatenate with ". " ensuring no double punctuation; capitalize
    sensibly is not required (ECTOR normalizes).
3.3 If fewer than 2 samples for the chosen language, fall back to a single
    sample.
3.4 Deterministic-enough but varied: use `Math.random`; pick language by random
    among available languages that have >= 2 samples.
- Verify: clicking produces a longer combined request and a populated JSON.

## Element 4 — "Random pick" (switches language)
4.1 Button near examples. On click: choose a random sample across ALL languages
    (so it switches between en/fr/...), fill textarea, set lang selector to that
    sample's lang, auto-compute, flash the textarea.
4.2 Avoid repeating the immediately previous pick when possible.
- Verify: repeated clicks vary text and sometimes switch language.

## Element 5 — Layout / polish
5.1 Group the new action buttons ("Combine", "Random") in the examples header
    row, right-aligned; keep example chips below.
5.2 Keep textarea compact (130px, resizable) per previous request.
5.3 Accessibility: buttons have `title`/`aria-label`; counter has
    `aria-live="polite"`.
5.4 Theme toggle has `aria-label` and reflects state.

## Element 6 — Tests
6.1 Backend: `tests/test_web.py` — add tokenize tests (counts for a known
    string; unknown-lang fallback; empty text → zeros).
6.2 No JS unit harness in repo; rely on backend tests + manual live check
    (curl + server) for front-end wiring.

## Verification gates
- `ruff check .` clean (web app is Python; JS/CSS not linted by ruff).
- `pytest` green (incl. new tokenize tests).
- Live server: counts endpoint returns sane values; page serves; theme/combine/
  random verified by serving and curling assets.
