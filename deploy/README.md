# Deploying the ECTOR web showcase

Two supported paths: a **systemd + Caddy** deployment (like
[shhx.dev](https://github.com/Sanix-Darker/shhx.dev)) for a VM/bare host, or
**Docker Compose** (app + Caddy) for a container host.

The core `ector` library has no web dependencies; the demo uses the optional
`web` extra (FastAPI + uvicorn). The endpoint is unauthenticated — always front
it with Caddy and add rate limiting if exposed publicly.

---

## Option A — systemd + Caddy (bare host)

1. **Create a user and app dir**
   ```bash
   sudo useradd --system --home /opt/ector --shell /usr/sbin/nologin ector
   sudo mkdir -p /opt/ector /etc/ector
   sudo chown -R ector:ector /opt/ector
   ```

2. **Get the code + a virtualenv with models**
   ```bash
   sudo -u ector git clone https://github.com/Sanix-Darker/ector /opt/ector
   cd /opt/ector
   sudo -u ector python3.12 -m venv .venv
   sudo -u ector .venv/bin/pip install ".[web]"
   sudo -u ector .venv/bin/python -m spacy download en_core_web_sm
   sudo -u ector .venv/bin/python -m spacy download fr_core_news_sm
   ```

3. **Environment**
   ```bash
   sudo cp deploy/ector.env.example /etc/ector/ector.env
   sudo $EDITOR /etc/ector/ector.env   # set HOST/PORT/WORKERS
   ```

4. **systemd unit**
   ```bash
   sudo cp deploy/ector-web.service /etc/systemd/system/ector-web.service
   sudo systemctl daemon-reload
   sudo systemctl enable --now ector-web
   sudo systemctl status ector-web
   ```

5. **Caddy**
   ```bash
   sudo cp deploy/Caddyfile.example /etc/caddy/Caddyfile
   sudo $EDITOR /etc/caddy/Caddyfile   # replace example.com with your domain
   sudo systemctl reload caddy
   ```
   For a real public domain, remove `tls internal` so Caddy provisions a
   Let's Encrypt certificate automatically.

---

## Option B — Docker Compose (app + Caddy)

```bash
cp deploy/Caddyfile.example deploy/Caddyfile
# For Docker compose mode, Caddy must proxy to `ector-web:8000`.
# (In the copied Caddyfile this can be done by replacing `127.0.0.1:8000`.)
$EDITOR deploy/Caddyfile   # set your domain

cd deploy
docker compose up -d
```

## Option C — GHCR image deployment (recommended)

```bash
docker pull ghcr.io/sanix-darker/ector:latest
cd deploy
docker compose up -d
```

The app image (`deploy/Dockerfile`) installs `ector[web,models]` and is self-contained/offline at runtime.

For local source builds (useful for validating changes), use:

```bash
cd deploy
ECTOR_IMAGE=ector-web:dev \
  docker compose -f docker-compose.yml -f docker-compose.local.yml up --build -d
```

The CI workflow `.github/workflows/docker.yml` publishes:
`ghcr.io/sanix-darker/ector:latest` and `ghcr.io/sanix-darker/ector:<sha>`
on every push to `master`.

---

## Files

| File | Purpose |
|------|---------|
| `Caddyfile.example` | Caddy HTTPS reverse proxy (gzip, content-types, www redirect) |
| `ector-web.service` | Hardened systemd unit running uvicorn from the venv |
| `ector.env.example` | HOST/PORT/WORKERS + model notes |
| `Dockerfile` | Self-contained app image (uvicorn + models) |
| `docker-compose.yml` | App + Caddy stack |

## Notes
- The first request after a (re)start pays the spaCy model load (~200 ms); it is
  cached per worker afterwards (≈2 ms/request).
- Each uvicorn worker loads its own model copy; 1–2 workers is plenty for a demo.
- Health check: `GET /api/health` returns version, languages, and repo URL.
