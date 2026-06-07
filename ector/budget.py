"""Budget detection and assembly.

Language-aware (BUG-001): budget hints are taken from the active
:class:`LanguageConfig`, so French budget phrases work. Budgets are emitted even
without a currency, mirroring how product prices are handled (BUG-008).

See ``docs/features/02-budget-detection.md``.
"""

from __future__ import annotations

import re

from ector.fuzzy import bounded_levenshtein
from ector.languages import LanguageConfig
from ector.types import Budget

# The literal word "budget" is a budget signal in both supported languages.
_BUDGET_WORD = re.compile(r"(?<!\w)budget(?!\w)", re.IGNORECASE)

# Anchor words whose presence (exactly or via a close typo) strongly signals a
# budget context. Kept short and high-precision.
_BUDGET_ANCHORS_EN = ("budget", "only", "afford", "spend", "maximum")
_BUDGET_ANCHORS_FR = ("budget", "seulement", "depasser", "maximum", "plafond")
_WORD_RE = re.compile(r"[^\W\d_]+", re.UNICODE)


def _fuzzy_has_anchor(text: str, anchors: tuple[str, ...]) -> bool:
    """True if any token in ``text`` is, or is a close typo of, an anchor word."""
    for token in _WORD_RE.findall(text.lower()):
        if len(token) < 3:
            continue
        for anchor in anchors:
            md = 1 if len(anchor) <= 6 else 2
            if abs(len(token) - len(anchor)) > md:
                continue
            if bounded_levenshtein(token, anchor, md) <= md:
                return True
    return False


def is_budget(text: str, config: LanguageConfig) -> bool:
    """Heuristic: does ``text`` indicate a spending limit?

    True when the word "budget" appears (word-boundary), any language-specific
    budget hint is present, or a fuzzy budget anchor word matches (typo-robust).
    """
    lowered = text.lower()
    if _BUDGET_WORD.search(lowered):
        return True
    if any(hint in lowered for hint in config.budget_hints):
        return True
    anchors = _BUDGET_ANCHORS_FR if config.code == "fr" else _BUDGET_ANCHORS_EN
    return _fuzzy_has_anchor(lowered, anchors)


def build_budget(price: float | None, currency: str | None) -> Budget | None:
    """Build a budget dict from a price/currency, or ``None`` if not valid.

    A budget is valid when ``price`` is a positive number. Currency is optional
    (BUG-008): "my budget is 300" yields ``{"price": 300.0}``.
    """
    if price is None or price <= 0:
        return None
    budget: Budget = {"price": price}
    if currency is not None:
        budget["currency"] = currency
    return budget
