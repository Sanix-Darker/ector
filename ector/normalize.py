"""Functional-vocabulary normalization (pre-spaCy typo correction).

Corrects ONLY closed-class / known vocabulary to canonical spelling so that both
ECTOR's detectors and spaCy's parser behave well on noisy input. Unknown
open-vocabulary tokens are left untouched (D-08-1).

Corrected classes per language:
- currency words (and known misspellings),
- the budget keyword,
- high-signal trigger verbs (look/want/need/buy/...),
- connectors/units (and/et, qty, pcs),
- curated catalog nouns + brands.

See ``docs/features/08-typo-tolerance.md``.
"""

from __future__ import annotations

import re
from functools import lru_cache

from ector.dictionary import CURRENCY_MISSPELLINGS, CURRENCY_WORDS
from ector.dictionary.catalog import catalog_terms_for
from ector.dictionary.common_words import is_common_word
from ector.fuzzy import FuzzyIndex, threshold_for

# High-signal trigger verbs/words worth correcting (kept small + safe).
_TRIGGER_WORDS_EN = {
    "looking", "look", "want", "wanted", "need", "needed", "buy", "buying",
    "purchase", "searching", "search", "find", "get", "order", "ordering",
    "interested", "shopping", "budget", "have", "spend", "afford",
}
_TRIGGER_WORDS_FR = {
    "cherche", "chercher", "veux", "vouloir", "besoin", "acheter", "achète",
    "commander", "trouver", "budget", "depenser", "dépenser", "regarde",
    "voudrais", "aimerais",
}

# Connectors / units that benefit from correction.
_CONNECTORS = {"and", "et", "or", "ou", "with", "avec", "plus", "also", "aussi"}
_UNITS = {"qty", "pcs", "units", "pieces", "pack", "packs"}

# Tokens we never attempt to correct (very short or numeric handled elsewhere).
_TOKEN_RE = re.compile(r"[A-Za-zÀ-ÿ]+")


def _build_index(lang: str) -> FuzzyIndex:
    terms: set[str] = set()
    terms |= set(CURRENCY_WORDS)
    terms |= set(CURRENCY_MISSPELLINGS)  # so a misspelling maps to itself fast
    terms |= set(_CONNECTORS)
    terms |= set(_UNITS)
    if lang == "fr":
        terms |= _TRIGGER_WORDS_FR
    else:
        terms |= _TRIGGER_WORDS_EN
    terms |= set(catalog_terms_for(lang))
    return FuzzyIndex(terms)


def _functional_terms(lang: str) -> frozenset[str]:
    """Closed-class vocabulary that is always a valid correction target, even if
    it also appears in the common-words stop-list (e.g. 'want', 'need')."""
    base = set(CURRENCY_WORDS) | set(_CONNECTORS) | set(_UNITS)
    base |= _TRIGGER_WORDS_FR if lang == "fr" else _TRIGGER_WORDS_EN
    return frozenset(base)


@lru_cache(maxsize=4)
def _index_for(lang: str) -> FuzzyIndex:
    return _build_index(lang)


@lru_cache(maxsize=8192)
def _correct_token(token_lower: str, lang: str) -> str | None:
    """Return the canonical form for a token, or ``None`` if no confident match.

    Exact members return themselves; otherwise a bounded fuzzy match is tried.
    Currency misspellings resolve to their canonical currency word.
    """
    index = _index_for(lang)
    if token_lower in index:
        return CURRENCY_MISSPELLINGS.get(token_lower, token_lower)
    # Never rewrite a legitimate common word (avoids "take" -> "cake"), unless it
    # is itself functional vocabulary we deliberately correct toward.
    if is_common_word(token_lower, lang) and token_lower not in _functional_terms(lang):
        return None
    # Don't try to fuzzy-correct very short tokens (too ambiguous).
    if len(token_lower) < 4:
        return None
    match = index.best_match(token_lower, threshold_for(token_lower))
    if match is None:
        return None
    # Reject a correction that lands on a generic common word (e.g. "take" ->
    # "cake"); but allow landing on functional vocabulary ("wnat" -> "want").
    if is_common_word(match, lang) and match not in _functional_terms(lang):
        return None
    return CURRENCY_MISSPELLINGS.get(match, match)


def _preserve_case(original: str, corrected: str) -> str:
    """Apply the original token's casing pattern to the corrected token."""
    if original.isupper() and len(original) > 1:
        return corrected.upper()
    if original[:1].isupper():
        return corrected[:1].upper() + corrected[1:]
    return corrected


def normalize_vocabulary(text: str, lang: str = "en") -> str:
    """Correct known/closed-class tokens in ``text`` to canonical spelling.

    Unknown tokens are returned unchanged. Casing and all non-word characters
    (spaces, punctuation, digits) are preserved.

    Examples:
        >>> normalize_vocabulary("I'm lookng for a labtop", "en")
        "I'm looking for a laptop"
        >>> normalize_vocabulary("budjet of 100 dollr", "en")
        'budget of 100 dollar'
        >>> normalize_vocabulary("je veux un ordinateu", "fr")
        'je veux un ordinateur'
    """
    def repl(match: re.Match[str]) -> str:
        word = match.group(0)
        lower = word.lower()
        corrected = _correct_token(lower, lang)
        if corrected is None or corrected == lower:
            return word
        return _preserve_case(word, corrected)

    return _TOKEN_RE.sub(repl, text)
