# ECTOR web showcase image. Build from the repo root:
#   docker build -f deploy/Dockerfile -t ector-web .
#   docker run -p 8000:8000 ector-web
FROM python:3.12-slim

# System deps kept minimal; spaCy wheels are prebuilt.
ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    HOST=0.0.0.0 \
    PORT=8000 \
    WORKERS=1

WORKDIR /app
COPY . /app

# Install the package with web + model extras, then the models explicitly so the
# image is self-contained and offline at runtime.
RUN pip install --upgrade pip \
    && pip install ".[web]" \
    && python -m spacy download en_core_web_sm \
    && python -m spacy download fr_core_news_sm

EXPOSE 8000

# Shell form so ${HOST}/${PORT}/${WORKERS} expand from the environment.
CMD uvicorn web.app:app --host ${HOST} --port ${PORT} --workers ${WORKERS}
