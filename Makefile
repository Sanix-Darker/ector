# ECTOR - developer & deployment tasks.
# Uses the project virtualenv at .venv (create with `make install`).

VENV    := .venv
PY      := $(VENV)/bin/python
PIP     := $(VENV)/bin/pip
HOST    ?= 127.0.0.1
PORT    ?= 8000
WORKERS ?= 1

.PHONY: help install models run serve test lint fmt bench measure clean

help:
	@echo "Targets:"
	@echo "  install  Create venv and install ector[web] + dev tools"
	@echo "  models   Download spaCy language models"
	@echo "  run      Run the web app (dev, autoreload) on $(HOST):$(PORT)"
	@echo "  serve    Run the web app (prod-ish, $(WORKERS) worker(s))"
	@echo "  test     Run the test suite"
	@echo "  lint     Run ruff"
	@echo "  fmt      Auto-fix lint issues"
	@echo "  bench    Throughput/latency micro-benchmark"
	@echo "  measure  Quality metrics on the 12k fixture corpus"
	@echo "  clean    Remove caches and build artifacts"

install:
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -e ".[web]"
	$(PIP) install pytest ruff
	@echo "Now run: make models"

models:
	$(PY) -m spacy download en_core_web_sm
	$(PY) -m spacy download fr_core_news_sm

run:
	$(VENV)/bin/uvicorn web.app:app --reload --host $(HOST) --port $(PORT)

serve:
	$(VENV)/bin/uvicorn web.app:app --host $(HOST) --port $(PORT) --workers $(WORKERS)

test:
	$(PY) -m pytest

lint:
	$(VENV)/bin/ruff check .

fmt:
	$(VENV)/bin/ruff check . --fix

bench:
	$(PY) scripts/bench.py

measure:
	$(PY) scripts/measure.py

clean:
	rm -rf build dist *.egg-info .pytest_cache .ruff_cache
	find . -type d -name __pycache__ -not -path "./.venv/*" -exec rm -rf {} + 2>/dev/null || true
