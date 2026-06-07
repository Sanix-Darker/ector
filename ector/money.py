"""Money parsing: the single source of truth for price + currency extraction.

Handles messy real-world formats (see docs/features/08-typo-tolerance.md):
- decimal comma/point, thousands separators ("1,000", "1 000", "9,99"),
- attached symbols/codes ("$25", "25$", "25usd", "€9.99"),
- shorthand ("1k", "2.5k"),
- spelled-out amounts ("twenty dollars", "deux cents euros"),
- fuzzy-corrected misspelled currency words ("dollr" -> usd).
"""

from __future__ import annotations

import re

from ector.dictionary import (
    AMOUNT_WITH_CURRENCY_PATTERN,
    CURRENCY_MAP,
    CURRENCY_MISSPELLINGS,
    CURRENCY_ONLY_PATTERN,
    CURRENCY_WORDS,
    SYMBOL_PREFIX_PATTERN,
)
from ector.dictionary.numbers import (
    EN_NUMBER_FILLERS,
    FR_NUMBER_FILLERS,
    number_vocab,
)
from ector.fuzzy import FuzzyIndex, cached_best_match, register_index
from ector.types import Currency, Price

# Fuzzy index over currency words, for correcting misspellings like "dollr".
_CURRENCY_INDEX = FuzzyIndex(list(CURRENCY_WORDS) + list(CURRENCY_MISSPELLINGS))
_CURRENCY_TOKEN = register_index(_CURRENCY_INDEX)

# "1k" / "2.5k" shorthand, but ONLY when adjacent to a currency token/symbol so
# that resolution specs like "4k HD" are never read as money. The currency may
# come immediately before (e.g. "$2k") or after (e.g. "2k usd", "2k$").
_CURRENCY_AFTER = r"(?:\$|€|£|¥|₹|₩|₽|₺|₦|usd|eur|gbp|jpy|cad|aud|inr|chf|cny|krw|sar|aed|rub|brl|zar|mxn|sek|nok|dkk|pln|try|ngn|dollars?|euros?|pounds?|bucks?|quid|yen|rupees?|francs?|balles?)"
# "<amount>k" followed by a currency (optional space). Symbols need no \b;
# word currencies get a trailing word boundary.
_SHORTHAND_K = re.compile(
    rf"(?<![\w.])(\d+(?:[.,]\d+)?)\s*[kK]\s*(?=(?:[$€£¥₹₩₽₺₦]|{_CURRENCY_AFTER}\b))",
    re.IGNORECASE,
)
# "<symbol><amount>k" e.g. "$2k", "€1.5k".
_SHORTHAND_K_SYMBOL = re.compile(
    r"([$€£¥₹₩₽₺₦])\s*(\d+(?:[.,]\d+)?)\s*[kK]\b",
    re.IGNORECASE,
)
# Bare "Nk" with no currency context (used only by budget allow_bare path).
_SHORTHAND_K_BARE = re.compile(r"(?<![\w.])(\d+(?:[.,]\d+)?)\s*[kK]\b(?![a-zA-Z])")
# A number possibly with thousands separators / decimal, immediately followed by
# letters (e.g. "25usd", "9eur").
_AMOUNT_GLUED_WORD = re.compile(r"(\d+(?:[.,]\d+)?)([a-zA-Z]{2,5})")
# A number, a space, then a word (candidate possibly-misspelled currency word).
_AMOUNT_THEN_WORD = re.compile(r"(\d+(?:[.,]\d+)?)\s+([a-zA-Z]{3,9})")

# Number words that are also articles; not treated as a price when standalone.
_ARTICLE_LIKE_NUMBERS = frozenset({"a", "one", "un", "une"})


def normalize_currency(token: str | None) -> Currency:
    """Map a raw currency token/symbol to a normalized lowercase code.

    Applies exact map, known-misspelling map, then bounded fuzzy correction.
    Returns ``None`` for an empty/unknown token.

    Examples:
        >>> normalize_currency("dollars")
        'usd'
        >>> normalize_currency("€")
        'eur'
        >>> normalize_currency("dollr")
        'usd'
        >>> normalize_currency("")
        >>> normalize_currency(None)
    """
    if not token:
        return None
    key = token.strip().lower()
    if not key:
        return None
    if key in CURRENCY_MAP:
        return CURRENCY_MAP[key]
    if key in CURRENCY_MISSPELLINGS:
        return CURRENCY_MAP.get(CURRENCY_MISSPELLINGS[key])
    # Fuzzy: correct a misspelled currency word to a known one.
    match = cached_best_match(_CURRENCY_TOKEN, key)
    if match is not None:
        canonical = CURRENCY_MISSPELLINGS.get(match, match)
        if canonical in CURRENCY_MAP:
            return CURRENCY_MAP[canonical]
    return None


def _to_float(amount_str: str) -> float | None:
    """Parse a numeric string that may contain thousands/decimal separators.

    Heuristics:
    - "1,000" / "1 000" -> 1000 (thousands separators)
    - "9,99" -> 9.99 (decimal comma) when the comma group is not 3 digits
    - "1,234.56" -> 1234.56 (comma thousands + dot decimal)
    """
    s = amount_str.strip().replace(" ", "")
    if not s:
        return None

    has_dot = "." in s
    has_comma = "," in s
    try:
        if has_dot and has_comma:
            # Last separator is the decimal point.
            if s.rfind(",") > s.rfind("."):
                s = s.replace(".", "").replace(",", ".")
            else:
                s = s.replace(",", "")
        elif has_comma:
            parts = s.split(",")
            # comma as decimal if the final group is not exactly 3 digits
            if len(parts) == 2 and len(parts[1]) != 3:
                s = s.replace(",", ".")
            else:
                s = s.replace(",", "")
        # dot-only or no separator: leave as-is
        return float(s)
    except ValueError:
        return None


def _spelled_out_amount(text: str, lang: str) -> float | None:
    """Parse a spelled-out amount like "two hundred" / "deux cents".

    Scans for a maximal run of number words and folds them into an integer.
    Returns ``None`` if no number words are present.

    Guard: a lone unit word that doubles as an article ("a"/"one"/"un"/"une") is
    NOT treated as an amount, because in practice these are articles, not prices.
    Such words only count when part of a longer number run (e.g. "one hundred").
    """
    vocab = number_vocab(lang)
    fillers = FR_NUMBER_FILLERS if lang == "fr" else EN_NUMBER_FILLERS
    tokens = re.findall(r"[a-zàâçéèêëîïôûùüÿñæœ-]+", text.lower())

    run_words: list[str] = []
    current = 0
    result = 0
    found = False
    for tok in tokens:
        if tok in fillers and found:
            continue
        if tok not in vocab:
            if found:
                break
            continue
        found = True
        run_words.append(tok)
        value = vocab[tok]
        if value == 100:
            current = (current or 1) * 100
        elif value >= 1000:
            current = (current or 1) * value
            result += current
            current = 0
        else:
            current += value
    if not found:
        return None
    # Reject a lone article-like number word ("a"/"one"/"un"/"une").
    if len(run_words) == 1 and run_words[0] in _ARTICLE_LIKE_NUMBERS:
        return None
    return float(result + current)


def parse_price(text: str, *, allow_bare: bool = False, lang: str = "en") -> tuple[Price, Currency]:
    """Parse the first relevant amount + currency from ``text``.

    By default (``allow_bare=False``) a number is only returned when it is
    adjacent to a currency token/symbol (avoids treating quantities as prices,
    BUG-010). ``allow_bare=True`` also accepts a standalone number and a
    spelled-out amount (used by budget detection).

    Examples:
        >>> parse_price("It costs 100 USD.")
        (100.0, 'usd')
        >>> parse_price("It's 25$")
        (25.0, 'usd')
        >>> parse_price("$1,000")
        (1000.0, 'usd')
        >>> parse_price("9,99 eur")
        (9.99, 'eur')
        >>> parse_price("25usd")
        (25.0, 'usd')
        >>> parse_price("2.5k usd")
        (2500.0, 'usd')
        >>> parse_price("No price here")
        (None, None)
        >>> parse_price("I want 2 phones")
        (None, None)
        >>> parse_price("my budget is 300", allow_bare=True)
        (300.0, None)
        >>> parse_price("twenty dollars")
        (20.0, 'usd')
    """
    # 1) shorthand "1k"/"2.5k" only when adjacent to a currency ("2k usd", "$2k")
    if sym_k := _SHORTHAND_K_SYMBOL.search(text):
        base = _to_float(sym_k.group(2))
        if base is not None:
            return base * 1000, normalize_currency(sym_k.group(1))
    if sh := _SHORTHAND_K.search(text):
        base = _to_float(sh.group(1))
        if base is not None:
            amount = base * 1000
            tail = text[sh.end():]
            currency = _first_currency_token(tail) or _first_currency_token(text)
            return amount, currency

    # 2) "<symbol><amount>" e.g. "$25", "€9.99", "₹1,000"
    if sym := SYMBOL_PREFIX_PATTERN.search(text):
        value = _to_float(sym.group(2))
        if value is not None:
            return value, normalize_currency(sym.group(1))

    # 3) "<amount><currency>" with adjacent currency token (word or symbol)
    if cur := AMOUNT_WITH_CURRENCY_PATTERN.search(text):
        value = _to_float(cur.group(1))
        if value is not None:
            return value, normalize_currency(cur.group(2))

    # 4) number glued to a (possibly misspelled) currency word: "25usd", "9eur"
    for m in _AMOUNT_GLUED_WORD.finditer(text):
        currency = normalize_currency(m.group(2))
        if currency is not None:
            value = _to_float(m.group(1))
            if value is not None:
                return value, currency

    # 4b) number followed (with space) by a word that fuzzy-matches a currency,
    # e.g. "25 dollr", "9 euoros". The regex alternation only contains canonical
    # tokens, so misspellings need this explicit number+word scan.
    for m in _AMOUNT_THEN_WORD.finditer(text):
        currency = normalize_currency(m.group(2))
        if currency is not None:
            value = _to_float(m.group(1))
            if value is not None:
                return value, currency

    # 5) spelled-out amount with a currency word somewhere ("twenty dollars")
    spelled = _spelled_out_amount(text, lang)
    if spelled is not None:
        currency = _first_currency_token(text)
        if currency is not None or allow_bare:
            return spelled, currency

    # 6) bare number (only when explicitly allowed). Rejects junk like "12x34".
    if allow_bare:
        from ector.dictionary import BARE_AMOUNT_PATTERN

        # bare shorthand "Nk" (e.g. "budget 2k") -> N*1000
        if sh := _SHORTHAND_K_BARE.search(text):
            base = _to_float(sh.group(1))
            if base is not None:
                return base * 1000, None
        if match := BARE_AMOUNT_PATTERN.search(text):
            value = _to_float(match.group(1))
            if value is not None:
                return value, None

    return None, None


def _first_currency_token(text: str) -> Currency:
    """Return the normalized currency of the first currency token in ``text``."""
    m = CURRENCY_ONLY_PATTERN.search(text)
    if m:
        return normalize_currency(m.group(0))
    return None


def is_currency_only(name: str) -> bool:
    """True if ``name`` is *entirely* a currency token (after trimming).

    Full match (RISK-009 fix), so "pound cake" is NOT currency-only.

    Examples:
        >>> is_currency_only("usd")
        True
        >>> is_currency_only("  € ")
        True
        >>> is_currency_only("pound cake")
        False
        >>> is_currency_only("")
        False
    """
    trimmed = name.strip()
    if not trimmed:
        return False
    return CURRENCY_ONLY_PATTERN.fullmatch(trimmed) is not None
