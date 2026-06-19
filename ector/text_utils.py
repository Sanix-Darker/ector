"""Text normalization and phrase cleaning helpers.

Replaces the original ``replace_punctuation_with_fullstop`` (which destroyed
apostrophes and decimals - BUG-014) and ``clean_phrase`` (order-fragile filler
stripping - BUG-012).

See ``docs/features/01-product-extraction.md``.
"""

from __future__ import annotations

from collections.abc import Sequence
from functools import lru_cache

# Punctuation that should act as a sentence/clause separator. We convert these
# to a period so the per-sentence pipeline treats each clause independently.
# We deliberately do NOT touch:
#   - apostrophes (' and U+2019) -> needed for English/French contractions,
#   - hyphens -> needed for French ("est-ce", "peut-être"),
#   - decimal points -> needed for amounts like "9.99".
_SEGMENTERS = ",;:"
_SEGMENTER_SET = frozenset(_SEGMENTERS)

# Articles to strip from the start of a product phrase (English + French).
_ARTICLES = ("a ", "an ", "the ", "un ", "une ", "le ", "la ", "les ", "des ")


def normalize_text(text: str) -> str:
    """Normalize input for sentence segmentation without mangling tokens.

    Converts clause separators (``, ; :``) to periods so run-on clauses split
    into separate sentences, while preserving apostrophes, hyphens, decimal
    points, and *in-number* separators like the comma in "2,000" (BUG-014 and
    the thousands-separator fix).

    A separator is preserved (left as a comma) when it sits directly between two
    digits, so "2,000" stays intact; otherwise it becomes a period.

    Examples:
        >>> normalize_text("Hi, I'm looking for a laptop")
        "Hi. I'm looking for a laptop"
        >>> normalize_text("j'ai un budget de 9.99")
        "j'ai un budget de 9.99"
        >>> normalize_text("a phone; a charger")
        'a phone. a charger'
        >>> normalize_text("I want it for 2,000 usd")
        'I want it for 2,000 usd'
    """
    if not any(ch in _SEGMENTER_SET for ch in text):
        return text

    out: list[str] = []
    chars = text
    last_index = len(chars) - 1
    for i, ch in enumerate(chars):
        if ch in _SEGMENTERS:
            prev_digit = i > 0 and chars[i - 1].isdigit()
            next_digit = i < last_index and chars[i + 1].isdigit()
            # keep an in-number thousands separator (e.g. "2,000")
            if ch == "," and prev_digit and next_digit:
                out.append(ch)
            else:
                out.append(".")
        else:
            out.append(ch)
    return "".join(out)


@lru_cache(maxsize=32)
def _normalize_fillers(fillers: tuple[str, ...]) -> tuple[str, ...]:
    """Canonical, deterministic filler ordering with fast reuse across calls."""
    return tuple(sorted(set(fillers), key=len, reverse=True))


def clean_phrase(phrase: str, fillers: Sequence[str]) -> str:
    """Strip a leading filler phrase and article, trim, and capitalize.

    Deterministic (BUG-012 fix): tries fillers longest-first and removes at most
    one leading filler, then at most one leading article. ``fillers`` should be
    pre-sorted longest-first (the language registry guarantees this), but this
    function sorts defensively to remain correct regardless of input order.

    Examples:
        >>> clean_phrase("i need a big red apple", ["i need a", "i need"])
        'Big red apple'
        >>> clean_phrase("the laptop", [])
        'Laptop'
        >>> clean_phrase("  a phone ", [])
        'Phone'
    """
    result = phrase.strip()
    lowered = result.lower()

    # Remove at most one leading filler (longest match first).
    normalized_fillers = fillers if isinstance(fillers, tuple) else tuple(fillers)
    for filler in _normalize_fillers(normalized_fillers):
        prefix = filler + " "
        if lowered.startswith(prefix):
            result = result[len(prefix):].strip()
            lowered = result.lower()
            break

    # Remove at most one leading article.
    for article in _ARTICLES:
        if lowered.startswith(article):
            result = result[len(article):].strip()
            lowered = result.lower()
            break

    # Trim leading/trailing punctuation noise and surrounding whitespace.
    result = result.strip(".,!?;:").strip()

    if result:
        return result[0].upper() + result[1:]
    return result
