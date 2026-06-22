"""Classify the shopper's intent from the request text.

Coarse, keyword-driven, typo-tolerant classification into:
  - ``price_check``   : asking how much something costs
  - ``availability``  : asking whether something is available/in stock
  - ``compare``       : comparing options
  - ``buy``           : wants to purchase / find a product (default for product
                        requests)
  - ``browse``        : generic looking with no strong signal

See ``docs/plan/06-richer-fields-and-web.md``.
"""

from __future__ import annotations

import re

_WORD_RE = re.compile(r"[^\W\d_]+", re.UNICODE)

# Phrase signals (substring match on lowercased text).
_PRICE_CHECK = (
    "how much", "what is the price", "what's the price", "price of", "cost of",
    "how much is", "how much are", "how much for", "what does it cost",
    "combien", "quel est le prix", "quel prix", "prix de", "coute", "coûte",
    "tarif", "what price",
)
_AVAILABILITY = (
    "in stock", "available", "availability", "do you have", "do you stock",
    "do you carry", "is there", "are there", "en stock", "disponible",
    "disponibilite", "disponibilité", "avez-vous", "est-ce que vous avez",
)
_COMPARE = (
    "compare", "comparison", "versus", " vs ", " vs. ", "difference between",
    "which is better", "better than",
    "comparer", "comparaison", "différence entre", "difference entre",
    "lequel choisir", "quelle difference",
)
_BUY = (
    "buy", "purchase", "order", "i want", "i need", "looking for", "looking to buy",
    "add to cart", "acheter", "commander", "je veux", "j'ai besoin", "je cherche",
    "je voudrais", "j'aimerais",
)

# Substring phrases that explicitly mark the request as browse even when
# products are mentioned (without these, "looking at watches" falls into the
# has_products -> "buy" fallback at the bottom of classify_intent).
_BROWSE_OVERRIDE = (
    "looking at", "just looking", "browsing",
    "juste regarder", "juste pour regarder",
)


def _has_any(text: str, phrases: tuple[str, ...]) -> bool:
    return any(p in text for p in phrases)


def classify_intent(text: str, has_products: bool) -> str:
    """Return a coarse intent label for ``text``.

    Order of precedence: price_check > availability > compare > buy > browse.
    """
    low = f" {text.lower()} "

    if _has_any(low, _PRICE_CHECK):
        return "price_check"
    if _has_any(low, _AVAILABILITY):
        return "availability"
    if _has_any(low, _COMPARE):
        return "compare"
    if _has_any(low, _BUY):
        return "buy"
    # Word-boundary override: only short single-word keys like "browsing" can
    # substring-collide (e.g. "I'm browsing the catalogue to find a deal"); the
    # two-word phrases ("looking at", "just looking", ...) are specific enough
    # to use plain substring.
    if any(re.search(rf"\b{re.escape(p)}\b", low) for p in _BROWSE_OVERRIDE
           if " " not in p):
        return "browse"
    for p in _BROWSE_OVERRIDE:
        if " " in p and p in low:
            return "browse"
    return "buy" if has_products else "browse"
