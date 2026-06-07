# Plan 10 — Deployment (modeled on shhx.dev)

shhx.dev ships `deploy/Caddyfile.example`, `deploy/<svc>.service` (hardened
systemd), `deploy/<svc>.env.example`, plus a Makefile with build/run targets and
a reverse proxy on a fixed port. ECTOR's web app is Python/FastAPI, so we mirror
the *conventions* (Caddy HTTPS reverse proxy + gzip + content-type headers + www
redirect; hardened systemd unit; env file; Makefile targets) adapted to uvicorn.

## Chunks

### D1 — `deploy/Caddyfile.example`
- http -> https redirect for apex + www.
- `https://example.com` reverse_proxy to the uvicorn port (8000).
- `encode gzip`, strip `Server` header, explicit content-types for css/js/svg.
- `tls internal` placeholder with a comment to swap for real certs / ACME.

### D2 — `deploy/ector-web.service` (systemd, hardened)
- Type=simple, dedicated User/Group `ector`.
- WorkingDirectory=/opt/ector; EnvironmentFile=-/etc/ector/ector.env.
- ExecStart runs uvicorn from the venv binding 127.0.0.1:${PORT}.
- Hardening: NoNewPrivileges, PrivateTmp, ProtectSystem=strict, ProtectHome,
  ReadWritePaths for the app dir.
- Restart=always, RestartSec=3, After/Wants network-online.

### D3 — `deploy/ector.env.example`
- HOST, PORT, ECTOR_AUTO_DOWNLOAD note, WORKERS.

### D4 — `Makefile` targets (repo root)
- `install` (venv + deps + models), `run` (uvicorn dev), `serve` (prod-ish),
  `test`, `lint`, `bench`, `measure`, `clean`. Use the project venv.

### D5 — `deploy/README.md`
- Step-by-step: build venv on server, install models, place env, install the
  systemd unit, point Caddy at it, reload. Security notes (unauthenticated demo;
  put behind Caddy; rate-limit if public).

### D6 — Optional Dockerfile + compose
- A slim Dockerfile (python:3.12-slim) installing ector[web,models] and running
  uvicorn; a compose file wiring Caddy + app (like caddy-fastapi pattern). Mark
  optional.

## Verification
- Caddyfile parses conceptually (syntax mirrors shhx's working example).
- systemd unit ExecStart path matches the documented layout.
- `make` targets run locally (at least `lint`, `test`, `measure`).
- Docker build is documented; not built here unless Docker is available.
