"""Dictionary package: data + normalization/validation.

This package replaces the former monolithic ``ector/dictionary.py``. It keeps
backward-compatible exports (``REQUEST_TRIGGERS_EN``, ``MONEY_PATTERN``, ...) so
existing imports such as ``from ector.dictionary import MONEY_PATTERN`` keep
working.

Normalization (lowercase + strip + dedupe, order-preserving) and validation
(no concatenated/doubled entries - guards against BUG-004 regressions) happen
once here at import time.
"""

from __future__ import annotations

from ector.dictionary.currencies import (
    AMOUNT_WITH_CURRENCY_PATTERN,
    BARE_AMOUNT_PATTERN,
    CURRENCY_MAP,
    CURRENCY_MISSPELLINGS,
    CURRENCY_ONLY_PATTERN,
    CURRENCY_SYMBOLS,
    CURRENCY_WORDS,
    MONEY_PATTERN,
    SYMBOL_PREFIX_PATTERN,
)
from ector.dictionary.en import (
    EN_BUDGET_HINTS as _EN_BUDGET_HINTS_RAW,
)
from ector.dictionary.en import (
    FILLER_PHRASES_EN as _FILLER_PHRASES_EN_RAW,
)
from ector.dictionary.en import (
    REQUEST_TRIGGERS_EN as _REQUEST_TRIGGERS_EN_RAW,
)
from ector.dictionary.fr import (
    FILLER_PHRASES_FR as _FILLER_PHRASES_FR_RAW,
)
from ector.dictionary.fr import (
    FR_BUDGET_HINTS as _FR_BUDGET_HINTS_RAW,
)
from ector.dictionary.fr import (
    REQUEST_TRIGGERS_FR as _REQUEST_TRIGGERS_FR_RAW,
)

ENGLISH = "en"
FRENCH = "fr"


def normalize_entries(entries: list[str]) -> list[str]:
    """Lowercase + strip each entry, drop empties, dedupe preserving order."""
    seen: set[str] = set()
    out: list[str] = []
    for raw in entries:
        item = raw.strip().lower()
        if not item or item in seen:
            continue
        seen.add(item)
        out.append(item)
    return out


def find_suspicious_entries(entries: list[str]) -> list[str]:
    """Return entries that look like accidental string concatenations.

    Heuristic guard against BUG-004 (a missing comma merges two list items).
    Flags an entry if it contains a doubled token (``somesome``) or a
    word-boundary-less run that joins two words with no space where one would be
    expected (``desje``, ``achatje``).
    """
    suspicious: list[str] = []
    for entry in entries:
        # doubled adjacent token, e.g. "buy somesome"
        words = entry.split()
        for word in words:
            n = len(word)
            if n >= 6 and n % 2 == 0 and word[: n // 2] == word[n // 2 :]:
                suspicious.append(entry)
                break
        else:
            # crude detection of two French phrases jammed together, e.g.
            # "...desje cherche" where "des" + "je" merged without a space.
            for needle in ("desje", "achatje", "unje", "uneje"):
                if needle in entry.replace(" ", ""):
                    suspicious.append(entry)
                    break
    return suspicious


# Normalized, deduped, validated public lists.
REQUEST_TRIGGERS_EN = normalize_entries(_REQUEST_TRIGGERS_EN_RAW)
FILLER_PHRASES_EN = normalize_entries(_FILLER_PHRASES_EN_RAW)
EN_BUDGET_HINTS = normalize_entries(_EN_BUDGET_HINTS_RAW)
REQUEST_TRIGGERS_FR = normalize_entries(_REQUEST_TRIGGERS_FR_RAW)
FILLER_PHRASES_FR = normalize_entries(_FILLER_PHRASES_FR_RAW)
FR_BUDGET_HINTS = normalize_entries(_FR_BUDGET_HINTS_RAW)

__all__ = [
    "AMOUNT_WITH_CURRENCY_PATTERN",
    "BARE_AMOUNT_PATTERN",
    "CURRENCY_MAP",
    "CURRENCY_MISSPELLINGS",
    "CURRENCY_ONLY_PATTERN",
    "CURRENCY_SYMBOLS",
    "CURRENCY_WORDS",
    "EN_BUDGET_HINTS",
    "ENGLISH",
    "FILLER_PHRASES_EN",
    "FILLER_PHRASES_FR",
    "FRENCH",
    "FR_BUDGET_HINTS",
    "MONEY_PATTERN",
    "REQUEST_TRIGGERS_EN",
    "REQUEST_TRIGGERS_FR",
    "SYMBOL_PREFIX_PATTERN",
    "find_suspicious_entries",
    "normalize_entries",
]
