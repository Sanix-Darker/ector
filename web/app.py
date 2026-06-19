"""FastAPI showcase for ECTOR.

A thin web layer over the ECTOR library: a JSON API plus a static single-page UI
that demonstrates natural-language -> structured e-commerce query parsing.

Run:
    pip install -e ".[web,models]"
    uvicorn web.app:app --reload
    # open http://127.0.0.1:8000

ECTOR itself has no web dependencies; FastAPI/uvicorn live in the optional
``web`` extra (see pyproject ``[project.optional-dependencies].web``).
"""

from __future__ import annotations

import logging
import os

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from ector import __version__, extract_sync
from ector.languages import get_language, supported_languages
from ector.models import get_model

_STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")

# Project metadata surfaced to the front-end.
REPO_URL = "https://github.com/Sanix-Darker/ector"

# Reject absurdly large payloads to keep the demo responsive.
MAX_TEXT_CHARS = 5000
_SUPPORTED_LANGS = frozenset(supported_languages())
_MODEL_READY: dict[str, bool] = {code: False for code in _SUPPORTED_LANGS}
_logger = logging.getLogger(__name__)


app = FastAPI(
    title="ECTOR",
    description="Fast, deterministic e-commerce request parser (NL -> structured query).",
    version=__version__,
)


def _normalize_lang(raw_lang: str | None) -> str:
    """Normalize incoming language code from public requests."""
    return str(raw_lang or "").strip().lower()


def _resolve_lang(raw_lang: str | None) -> str:
    """Resolve user-supplied language to supported defaults."""
    candidate = _normalize_lang(raw_lang)
    return candidate if candidate in _SUPPORTED_LANGS else "en"


@app.on_event("startup")
def _warm_models() -> None:
    for code in _SUPPORTED_LANGS:
        try:
            get_model(get_language(code).model_name)
        except OSError as exc:
            _logger.warning("Model warmup failed for %s: %s", code, exc)
            _MODEL_READY[code] = False
        else:
            _MODEL_READY[code] = True


class ExtractRequest(BaseModel):
    text: str = Field(default="", description="Free-form shopping request.")
    lang: str = Field(default="en", description="Language code (en|fr).")


class TokenizeRequest(BaseModel):
    text: str = Field(default="", description="Text to tokenize/count.")
    lang: str = Field(default="en", description="Language code (en|fr).")


# Curated placeholder examples surfaced in the UI.
EXAMPLES = [
    # --- English ---
    {"label": "Multi-product + budget (EN)",
     "lang": "en",
     "text": "Hi, I'm looking for a wireless gaming mouse and a mechanical keyboard, "
             "my budget is 150 usd"},
    {"label": "Typos everywhere (EN)",
     "lang": "en",
     "text": "i wnat an ipone and a chargr, budjet 200 euoros"},
    {"label": "Refurbished + price cap (EN)",
     "lang": "en",
     "text": "I want a refurbished macbook under 1200 usd"},
    {"label": "Between range (EN)",
     "lang": "en",
     "text": "looking for a 4k monitor between 300 and 500 eur"},
    {"label": "Price check (EN)",
     "lang": "en",
     "text": "how much is the new red nike air for size 42?"},
    {"label": "Quantity + total (EN)",
     "lang": "en",
     "text": "I need 3 wireless chargers and 2 usb cables, around 80 usd"},
    {"label": "Availability (EN)",
     "lang": "en",
     "text": "do you have a black leather sofa in stock?"},
    {"label": "Used, min price (EN)",
     "lang": "en",
     "text": "looking for a used iphone over 200 gbp"},
    {"label": "Shorthand price (EN)",
     "lang": "en",
     "text": "I want a gaming laptop for 2k usd"},
    {"label": "Slang currency (EN)",
     "lang": "en",
     "text": "need a pair of jordans, 150 bucks max"},

    # --- French ---
    {"label": "Budget + produits (FR)",
     "lang": "fr",
     "text": "je veux un velo neuf et un casque, mais j'ai un budget de 300 euros"},
    {"label": "Contrainte de prix (FR)",
     "lang": "fr",
     "text": "je cherche un ordinateur portable d'occasion moins de 600 euros"},
    {"label": "Fautes de frappe (FR)",
     "lang": "fr",
     "text": "je veu un ordinateu portable et une sourris, budjet 800 euros"},
    {"label": "Multi-produits (FR)",
     "lang": "fr",
     "text": "j'ai besoin d'un frigo, d'un micro-ondes et d'une cafetiere"},
    {"label": "Marque + couleur (FR)",
     "lang": "fr",
     "text": "je voudrais un iphone noir et des airpods, max 900 euros"},
    {"label": "Disponibilité (FR)",
     "lang": "fr",
     "text": "est-ce que vous avez une montre connectee en stock ?"},
    {"label": "Fourchette de prix (FR)",
     "lang": "fr",
     "text": "je cherche un televiseur entre 400 et 700 euros"},
    {"label": "Quantité (FR)",
     "lang": "fr",
     "text": "je veux 2 claviers et 3 souris sans fil pour 120 euros"},
    {"label": "Prix demandé (FR)",
     "lang": "fr",
     "text": "combien coute le nouveau samsung galaxy ?"},
    {"label": "Reconditionné (FR)",
     "lang": "fr",
     "text": "je veux un macbook reconditionne a partir de 800 euros"},
    {"label": "Budget seul (FR)",
     "lang": "fr",
     "text": "je n'ai qu'un budget de 250 dollars"},
    {"label": "Mélange complexe (FR)",
     "lang": "fr",
     "text": "bonjour, je cherche un grand canape gris en cuir, deux lampes et "
             "un tapis, mon budget total est de 1500 euros"},
]


@app.get("/api/health")
def health() -> dict:
    return {
        "status": "ok",
        "version": __version__,
        "languages": list(_SUPPORTED_LANGS),
        "model_ready": dict(_MODEL_READY),
        "models_loaded": all(_MODEL_READY.values()),
        "repo": REPO_URL,
        "max_chars": MAX_TEXT_CHARS,
    }


@app.get("/api/examples")
def examples() -> dict:
    return {"examples": EXAMPLES}


@app.post("/api/extract")
def extract_endpoint(req: ExtractRequest) -> JSONResponse:
    lang = _resolve_lang(req.lang)
    text = (req.text or "")[:MAX_TEXT_CHARS]
    try:
        result = extract_sync(text, lang)
    except OSError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return JSONResponse(result)


@app.post("/api/tokenize")
def tokenize_endpoint(req: TokenizeRequest) -> dict:
    """Return word and spaCy-token counts for the given text.

    Words = whitespace-ish split; tokens = spaCy tokenization (the units ECTOR
    actually reasons over). Cheap: only the tokenizer is exercised.
    """
    text = req.text or ""
    words = len(text.split())
    lang = _resolve_lang(req.lang)
    nlp = get_model(get_language(lang).model_name)
    # tokenizer.pipe is the cheapest path; count non-space tokens.
    doc = nlp.tokenizer(text[:MAX_TEXT_CHARS])
    tokens = sum(1 for t in doc if not t.is_space)
    chars = len(text)
    return {"words": words, "tokens": tokens, "chars": chars}


@app.get("/")
def index() -> FileResponse:
    return FileResponse(os.path.join(_STATIC_DIR, "index.html"))


# Serve static assets (CSS/JS) under /static.
app.mount("/static", StaticFiles(directory=_STATIC_DIR), name="static")
