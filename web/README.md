# ECTOR Web Showcase

A small FastAPI app + static single-page UI that demonstrates ECTOR parsing
natural-language shopping requests into structured JSON, live.

The core `ector` library has **no web dependencies**. FastAPI and uvicorn live in
the optional `web` extra.

## Run

```bash
# from the repo root, in your virtualenv
pip install -e ".[web,models]"

uvicorn web.app:app --reload
# open http://127.0.0.1:8000
```

## What it shows

- Left: a compact, resizable request textarea (so the examples and output stay
  in view), with a live counter under it: **words · tokens · chars**. The token
  count uses spaCy's tokenizer (the units ECTOR actually reasons over) via a
  debounced `/api/tokenize` call.
- Right: the structured JSON ECTOR extracts, in a **collapsible tree viewer**
  with line numbers — expand/collapse at every level (click a row or its caret),
  plus "Expand all" / "Collapse all" controls. Syntax-tinted; "Copy JSON" copies
  the full pretty output.
- A language selector (English / French).
- A **GitHub link** to the project source (also exposed via `/api/health`).
- 22 clickable placeholder examples, grouped by language (10 EN, 12 FR), that
  fill the input and auto-compute. Hover a chip to preview its full text.
- **🧩 Combine samples**: joins two random samples of the same language into one
  longer request and parses it.
- **🎲 Random pick**: picks a random sample across all languages (switches the
  language selector accordingly).
- **Light / dark theme** toggle (🌙 / ☀️), persisted in `localStorage` and
  defaulting to the system preference.
- A `pip install ector` banner with a copy button.
- Round-trip latency display.

## API

- `GET  /api/health` → `{status, version, languages}`
- `GET  /api/examples` → curated example requests
- `POST /api/extract` `{ "text": "...", "lang": "en" }` → ECTOR result JSON
- `POST /api/tokenize` `{ "text": "...", "lang": "en" }` → `{words, tokens, chars}`
- `GET  /` → the single-page UI
- `GET  /static/*` → CSS/JS assets

## Notes

- Everything runs locally and offline (after the spaCy models are installed).
- The endpoint is unauthenticated and intended for local/demo use. If you deploy
  it publicly, put it behind auth / rate limiting and restrict CORS as needed.

The container image can also be used directly:

```bash
docker pull ghcr.io/sanix-darker/ector:latest
docker run --rm -d --name ector-web -p 8000:8000 ghcr.io/sanix-darker/ector:latest
curl -X POST http://127.0.0.1:8000/api/extract \
  -H "Content-Type: application/json" \
  -d '{"text":"I want two refurbished laptops, budget 700 usd","lang":"en"}'
```

## Deployment

Production deployment files (Caddy reverse proxy, hardened systemd unit, env
example, Dockerfile, and docker-compose) live in [`../deploy/`](../deploy). See
[`../deploy/README.md`](../deploy/README.md) for systemd+Caddy and Docker Compose
walkthroughs. The conventions mirror
[shhx.dev](https://github.com/Sanix-Darker/shhx.dev)'s deploy setup, adapted from
Go to Python/uvicorn.
