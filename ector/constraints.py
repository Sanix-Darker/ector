"""Parse price constraints from a request.

Recognises max/min/around/between constraints in English and French, e.g.:
  - "under 200", "less than 200", "no more than 200", "up to 200", "200 max"
  - "over 50", "more than 50", "at least 50", "from 50"
  - "around 100", "about 100", "~100"
  - "between 100 and 200", "from 100 to 200", "entre 100 et 200"
  - FR: "moins de 200", "plus de 50", "environ 100", "à partir de 50", "max 200"

Returns a :class:`PriceConstraint` or ``None``. Typo tolerance for the amount is
provided by :func:`ector.money.parse_price`; the constraint keywords themselves
are matched with small typo tolerance via regex + fuzzy anchors.
"""

from __future__ import annotations

import re

from ector.money import _to_float, normalize_currency  # internal reuse
from ector.types import PriceConstraint

# A numeric amount (with separators / shorthand handled by _to_float + k).
_NUM = r"\d+(?:[.,\s]\d{3})*(?:[.,]\d+)?k?"

# "between X and Y" / "from X to Y" / "entre X et Y" / "de X a Y"
_BETWEEN = re.compile(
    rf"(?:between|from|entre|de)\s+({_NUM})\s*(?:and|to|et|[aà]|-|–)\s*({_NUM})",
    re.IGNORECASE,
)

# max constraints
_MAX = re.compile(
    rf"(?:under|below|less than|no more than|not more than|up to|at most|max(?:imum)?|"
    rf"moins de|au plus|jusqu'?[aà]|maxi?)\s*(?:of\s+)?({_NUM})",
    re.IGNORECASE,
)
# trailing "200 max" / "200 eur max" / "200 maximum"
_MAX_TRAILING = re.compile(
    rf"({_NUM})\s*(?:[a-z$€£¥₹₩₽₺₦]+\s*)?(?:max(?:imum)?|maxi)\b",
    re.IGNORECASE,
)

# min constraints
_MIN = re.compile(
    rf"(?:over|above|more than|at least|starting from|from|min(?:imum)?|"
    rf"plus de|au moins|[aà] partir de|mini?)\s*(?:of\s+)?({_NUM})",
    re.IGNORECASE,
)

# around constraints
_AROUND = re.compile(
    rf"(?:around|about|approximately|approx\.?|roughly|~|circa|environ|autour de|"
    rf"aux alentours de)\s*({_NUM})",
    re.IGNORECASE,
)


def _num(s: str) -> float | None:
    s = s.strip()
    mult = 1.0
    if s.lower().endswith("k"):
        mult = 1000.0
        s = s[:-1]
    val = _to_float(s)
    return val * mult if val is not None else None


def _currency_in(text: str) -> str | None:
    from ector.dictionary import CURRENCY_ONLY_PATTERN

    m = CURRENCY_ONLY_PATTERN.search(text)
    return normalize_currency(m.group(0)) if m else None


def parse_constraint(text: str) -> PriceConstraint | None:
    """Parse a price constraint from ``text`` or return ``None``.

    ``between`` is checked first (most specific), then around, then max, then min.
    The currency is taken from a window right after the matched amount(s) so that
    "budget 150 usd ... between 300 and 500 eur" yields ``eur`` for the
    constraint, not the unrelated earlier ``usd``.
    """

    def _currency_for(match) -> str | None:
        window = text[match.start(): match.end() + 8]
        return _currency_in(window) or _currency_in(text)

    if m := _BETWEEN.search(text):
        lo, hi = _num(m.group(1)), _num(m.group(2))
        if lo is not None and hi is not None:
            if lo > hi:
                lo, hi = hi, lo
            out: PriceConstraint = {"type": "between", "min": lo, "max": hi}
            currency = _currency_for(m)
            if currency:
                out["currency"] = currency
            return out

    if m := _AROUND.search(text):
        val = _num(m.group(1))
        if val is not None:
            out = {"type": "around", "value": val}
            currency = _currency_for(m)
            if currency:
                out["currency"] = currency
            return out

    for pat in (_MAX, _MAX_TRAILING):
        if m := pat.search(text):
            val = _num(m.group(1))
            if val is not None:
                out = {"type": "max", "value": val}
                currency = _currency_for(m)
                if currency:
                    out["currency"] = currency
                return out

    if m := _MIN.search(text):
        val = _num(m.group(1))
        if val is not None:
            out = {"type": "min", "value": val}
            currency = _currency_for(m)
            if currency:
                out["currency"] = currency
            return out

    return None
