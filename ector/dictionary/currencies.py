"""Currency data: normalization map and the money/currency regexes.

Single source of truth for currency tokens. See
``docs/features/03-currency-and-price-parsing.md`` and
``docs/features/08-typo-tolerance.md``.
"""

from __future__ import annotations

import re

# ---------------------------------------------------------------------------
# Canonical spellings/symbols -> normalized lowercase ISO-like code.
# ---------------------------------------------------------------------------
CURRENCY_MAP: dict[str, str] = {
    # USD
    "$": "usd",
    "us$": "usd",
    "usd": "usd",
    "dollar": "usd",
    "dollars": "usd",
    "buck": "usd",
    "bucks": "usd",
    # EUR
    "€": "eur",
    "eur": "eur",
    "euro": "eur",
    "euros": "eur",
    "balle": "eur",
    "balles": "eur",
    # GBP
    "£": "gbp",
    "gbp": "gbp",
    "pound": "gbp",
    "pounds": "gbp",
    "quid": "gbp",
    "sterling": "gbp",
    # JPY
    "¥": "jpy",
    "jpy": "jpy",
    "yen": "jpy",
    # CAD / AUD / NZD
    "cad": "cad",
    "c$": "cad",
    "aud": "aud",
    "a$": "aud",
    "nzd": "nzd",
    # CHF
    "chf": "chf",
    "franc": "chf",
    "francs": "chf",
    # INR
    "inr": "inr",
    "rupee": "inr",
    "rupees": "inr",
    "₹": "inr",
    # CNY
    "cny": "cny",
    "rmb": "cny",
    "yuan": "cny",
    # KRW
    "krw": "krw",
    "won": "krw",
    "₩": "krw",
    # Middle East
    "sar": "sar",
    "riyal": "sar",
    "riyals": "sar",
    "aed": "aed",
    "dirham": "aed",
    "dirhams": "aed",
    "dhs": "aed",
    # Others
    "rub": "rub",
    "ruble": "rub",
    "rubles": "rub",
    "₽": "rub",
    "brl": "brl",
    "real": "brl",
    "reais": "brl",
    "zar": "zar",
    "rand": "zar",
    "mxn": "mxn",
    "peso": "mxn",
    "pesos": "mxn",
    "sek": "sek",
    "nok": "nok",
    "dkk": "dkk",
    "pln": "pln",
    "zloty": "pln",
    "try": "try",
    "lira": "try",
    "₺": "try",
    "ngn": "ngn",
    "naira": "ngn",
    "₦": "ngn",
}

# ---------------------------------------------------------------------------
# Common misspellings -> the canonical currency word (which CURRENCY_MAP maps to
# a code). Used both directly and as fuzzy-index seeds.
# ---------------------------------------------------------------------------
CURRENCY_MISSPELLINGS: dict[str, str] = {
    "dollr": "dollar",
    "dollor": "dollar",
    "dolar": "dollar",
    "dollers": "dollars",
    "dollas": "dollars",
    "doller": "dollar",
    "doaller": "dollar",
    "euoro": "euro",
    "euoros": "euros",
    "eauro": "euro",
    "euros.": "euros",
    "eruo": "euro",
    "eruos": "euros",
    "puond": "pound",
    "puonds": "pounds",
    "pund": "pound",
    "ponds": "pounds",
    "rupe": "rupee",
    "rupies": "rupees",
    "rupess": "rupees",
    "yenn": "yen",
    "yyen": "yen",
    "dirhm": "dirham",
    "dirhem": "dirham",
    "riyel": "riyal",
    # Two-edit misspellings discovered on adversarial input (precision fix).
    # Each entry is at Damerau-Levenshtein distance 2 from its canonical
    # counterpart, which is past the default fuzzy threshold; explicit
    # entries are safer than bumping tolerance (which over-matches normal
    # English words like "found"->"pound", "ducks"->"bucks").
    "eors": "euros",
    "euors": "euros",
    "bucjsk": "bucks",
    "dollrr": "dollars",
    "pundse": "pounds",
}

# Words that are recognised as the currency-bearing terms (for fuzzy matching).
CURRENCY_WORDS: frozenset[str] = frozenset(
    w for w in CURRENCY_MAP if w.isalpha() and len(w) >= 3
)

# Currency symbols (used by regexes and the symbol-prefix matcher).
CURRENCY_SYMBOLS = "$€£¥₹₩₽₺₦"


def _alternation(tokens: list[str]) -> str:
    """Build a regex alternation, longest token first, escaping each token."""
    ordered = sorted(set(tokens), key=len, reverse=True)
    return "|".join(re.escape(tok) for tok in ordered)


# All recognised currency tokens (words + symbols + a few compound symbols).
_CURRENCY_TOKENS = list(CURRENCY_MAP.keys())
_CURRENCY_ALTERNATION = _alternation(_CURRENCY_TOKENS)

# Matches a currency token anywhere (used for guards / fullmatch).
CURRENCY_ONLY_PATTERN = re.compile(rf"(?:{_CURRENCY_ALTERNATION})", re.IGNORECASE)

# Matches an amount optionally followed by a currency token.
MONEY_PATTERN = re.compile(
    rf"(\d+(?:[.,]\d+)?)(?:\s*({_CURRENCY_ALTERNATION}))?",
    re.IGNORECASE,
)

# Matches "<symbol><amount>" forms like "$25" / "€9.99" / "₹1,000".
SYMBOL_PREFIX_PATTERN = re.compile(
    rf"([{re.escape(CURRENCY_SYMBOLS)}]|us\$|c\$|a\$)\s*(\d+(?:[.,\s]\d{{3}})*(?:[.,]\d+)?)",
    re.IGNORECASE,
)

# Matches "<amount><currency>" where a currency token is adjacent (symbol/word),
# allowing thousands separators and decimal comma/point.
AMOUNT_WITH_CURRENCY_PATTERN = re.compile(
    rf"(\d+(?:[.,\s]\d{{3}})*(?:[.,]\d+)?)\s*({_CURRENCY_ALTERNATION})",
    re.IGNORECASE,
)

# A standalone numeric amount that is NOT glued to letters/other digits, so junk
# like "12x34" does not yield a spurious "12". Allows thousands separators.
BARE_AMOUNT_PATTERN = re.compile(
    r"(?<![\w.,])(\d+(?:[.,\s]\d{3})*(?:[.,]\d+)?)(?![\w])"
)
