"""Detect brand, attributes, and condition within a product phrase.

Additive enrichment for the e-commerce parser (Feature 09). All detection is
typo-tolerant via the fuzzy indexes. Functions are pure and fast.

See ``docs/plan/06-richer-fields-and-web.md``.
"""

from __future__ import annotations

import re
from functools import lru_cache

from ector.dictionary.attributes import (
    CONDITION_MAP,
    all_attribute_words,
    colors,
    materials,
)
from ector.dictionary.catalog import BRANDS
from ector.fuzzy import FuzzyIndex, threshold_for

_WORD_RE = re.compile(r"[^\W\d_]+", re.UNICODE)
# Resolution / spec tokens that may contain digits (4k, 8k, 1080p, full-hd).
_SPEC_RE = re.compile(r"\b(\d{1,4}k|\d{3,4}p|full-?hd)\b", re.IGNORECASE)


@lru_cache(maxsize=2)
def _brand_index() -> FuzzyIndex:
    return FuzzyIndex(BRANDS)


@lru_cache(maxsize=4)
def _attr_index(lang: str) -> FuzzyIndex:
    return FuzzyIndex(all_attribute_words(lang))


@lru_cache(maxsize=4)
def _attr_set(lang: str) -> frozenset[str]:
    return all_attribute_words(lang)


_BRAND_SET = frozenset(BRANDS)


def detect_brand(phrase: str) -> str | None:
    """Return a recognised brand within ``phrase`` (typo-tolerant), or None."""
    index = _brand_index()
    for word in _WORD_RE.findall(phrase.lower()):
        if word in _BRAND_SET:
            return word
        if len(word) >= 4:
            match = index.best_match(word, threshold_for(word))
            if match is not None:
                return match
    return None


def detect_attributes(phrase: str, lang: str = "en") -> list[str]:
    """Return recognised attribute/descriptor words in ``phrase`` (canonicalised).

    Includes colors, sizes, materials, quality descriptors, and display/resolution
    specs (4k, 1080p, hd). Typo-tolerant. Results are ordered by first appearance
    and de-duplicated.
    """
    index = _attr_index(lang)
    known = _attr_set(lang)
    low = phrase.lower()
    found: list[tuple[int, str]] = []
    seen: set[str] = set()

    # spec tokens with digits (4k, 8k, 1080p, full-hd)
    for m in _SPEC_RE.finditer(low):
        spec = m.group(1)
        if spec in ("full-hd", "fullhd"):
            spec = "fhd"
        if spec not in seen:
            seen.add(spec)
            found.append((m.start(), spec))

    # alphabetic attribute words (with fuzzy tolerance)
    for m in re.finditer(r"[^\W\d_]+", low):
        word = m.group(0)
        canon: str | None = None
        if word in known:
            canon = word
        elif len(word) >= 4:
            canon = index.best_match(word, threshold_for(word))
        if canon and canon not in seen:
            seen.add(canon)
            found.append((m.start(), canon))

    found.sort(key=lambda t: t[0])
    return [w for _, w in found]


def detect_condition(text: str, lang: str = "en") -> str | None:
    """Return ``new`` | ``used`` | ``refurbished`` if a condition is mentioned.

    Checks multi-word phrases first ("brand new", "second hand", "remis à neuf"),
    then single words.
    """
    low = text.lower()
    # multi-word phrases first
    for phrase, value in CONDITION_MAP.items():
        if " " in phrase and phrase in low:
            return value
    words = set(_WORD_RE.findall(low))
    for phrase, value in CONDITION_MAP.items():
        if " " not in phrase and phrase in words:
            return value
    return None


def is_color(word: str, lang: str = "en") -> bool:
    return word.lower() in colors(lang)


def is_material(word: str, lang: str = "en") -> bool:
    return word.lower() in materials(lang)
