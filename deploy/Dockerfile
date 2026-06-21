# ECTOR web showcase image. Build from the repo root:
#   docker build -f deploy/Dockerfile -t ghcr.io/sanix-darker/ector:latest .
#   docker run -p 8000:8000 ghcr.io/sanix-darker/ector:latest
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONIOENCODING=UTF-8 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    HOST=0.0.0.0 \
    PORT=8000 \
    WORKERS=1

WORKDIR /app

# Copy source once; pip installs both FastAPI and the two spaCy runtime models.
COPY . /app

RUN pip install --upgrade pip \
    && pip install --no-cache-dir ".[web,models]"

# Run as non-root for a safer container runtime.
RUN groupadd --system --gid 10001 ector \
    && useradd --system --uid 10001 --gid 10001 --home /home/ector --create-home ector \
    && chown -R ector:ector /app
USER ector

EXPOSE 8000

# Keep container lifecycle simple: one process + JSON api health check.
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import urllib.request,sys; urllib.request.urlopen('http://127.0.0.1:' + __import__('os').environ.get('PORT','8000') + '/api/health').read(); sys.exit(0)"

# Shell form so HOST/PORT/WORKERS expand from the environment.
CMD uvicorn web.app:app --host ${HOST} --port ${PORT} --workers ${WORKERS}
