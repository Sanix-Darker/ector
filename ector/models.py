"""spaCy model management: cached loading + safe, opt-in download.

Fixes BUG-005 (model reloaded every call) via an ``lru_cache`` and BUG-006
(``python`` hardcoded; implicit runtime download) by using ``sys.executable`` and
making auto-download opt-in.

See ``docs/features/05-model-management-and-caching.md``.
"""

from __future__ import annotations

import logging
import os
import subprocess
import sys
from functools import cache

import spacy
from spacy.language import Language
from spacy.util import is_package

logger = logging.getLogger("ector.models")

# Environment flag that opts in to automatic model download on a cache miss.
AUTO_DOWNLOAD_ENV = "ECTOR_AUTO_DOWNLOAD"

# Pipeline components ECTOR does not use; disabled for speed. We rely on the
# tagger (pos_), parser (dep_ + sentence boundaries), attribute_ruler, and
# lemmatizer. Named-entity recognition is not used.
_DISABLED_PIPES = ("ner",)


def _auto_download_enabled() -> bool:
    return os.environ.get(AUTO_DOWNLOAD_ENV, "").strip().lower() in ("1", "true", "yes")


def download_model(model_name: str) -> None:
    """Download a spaCy model using the *current* interpreter.

    Uses ``sys.executable`` (BUG-006 fix) rather than a bare ``python`` which may
    not exist on the system.
    """
    logger.info("Downloading spaCy model %s", model_name)
    subprocess.run(
        [sys.executable, "-m", "spacy", "download", model_name],
        check=True,
    )


@cache
def get_model(model_name: str) -> Language:
    """Load and cache a spaCy pipeline by model name.

    The first call loads the model from disk; subsequent calls for the same model
    return the cached pipeline instantly (BUG-005 fix).

    If the model is not installed:
      - with ``ECTOR_AUTO_DOWNLOAD`` enabled, it is downloaded then loaded;
      - otherwise a clear, actionable :class:`OSError` is raised.
    """
    if not is_package(model_name):
        if _auto_download_enabled():
            download_model(model_name)
        else:
            raise OSError(
                f"spaCy model '{model_name}' is not installed. Install it with:\n"
                f"    {sys.executable} -m spacy download {model_name}\n"
                f"or install ECTOR's model extras: pip install 'ector[models]'.\n"
                f"Alternatively set {AUTO_DOWNLOAD_ENV}=1 to auto-download."
            )
    # Disable unused pipeline components (NER) for speed; ignore if absent.
    return spacy.load(model_name, exclude=list(_DISABLED_PIPES))


def clear_model_cache() -> None:
    """Clear the cached models (useful for tests)."""
    get_model.cache_clear()
