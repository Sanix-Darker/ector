"""Spelled-out number words for English and French.

Supports parsing amounts like "twenty dollars", "two hundred euros",
"deux cents euros", "mille". Covers the common e-commerce range (0-9999) which
is where spelled-out prices realistically occur.

See ``docs/features/08-typo-tolerance.md``.
"""

from __future__ import annotations

# English units, teens, tens, and scales.
EN_UNITS: dict[str, int] = {
    "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15,
    "sixteen": 16, "seventeen": 17, "eighteen": 18, "nineteen": 19,
}
EN_TENS: dict[str, int] = {
    "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50,
    "sixty": 60, "seventy": 70, "eighty": 80, "ninety": 90,
}
EN_SCALES: dict[str, int] = {
    "hundred": 100, "thousand": 1000, "k": 1000, "grand": 1000, "million": 1_000_000,
}

# French. Note 70/80/90 are compound in standard French; we include common forms.
FR_UNITS: dict[str, int] = {
    "zero": 0, "zéro": 0, "un": 1, "une": 1, "deux": 2, "trois": 3, "quatre": 4,
    "cinq": 5, "six": 6, "sept": 7, "huit": 8, "neuf": 9, "dix": 10,
    "onze": 11, "douze": 12, "treize": 13, "quatorze": 14, "quinze": 15,
    "seize": 16, "dix-sept": 17, "dix-huit": 18, "dix-neuf": 19,
}
FR_TENS: dict[str, int] = {
    "vingt": 20, "trente": 30, "quarante": 40, "cinquante": 50,
    "soixante": 60, "soixante-dix": 70, "quatre-vingt": 80, "quatre-vingts": 80,
    "quatre-vingt-dix": 90,
}
FR_SCALES: dict[str, int] = {
    "cent": 100, "cents": 100, "mille": 1000, "million": 1_000_000, "millions": 1_000_000,
}

# Connector words to ignore inside spelled-out numbers.
EN_NUMBER_FILLERS: frozenset[str] = frozenset({"and", "a"})
FR_NUMBER_FILLERS: frozenset[str] = frozenset({"et"})


def number_vocab(lang: str) -> dict[str, int]:
    """Return the merged unit/ten/scale vocab for a language."""
    if lang == "fr":
        return {**FR_UNITS, **FR_TENS, **FR_SCALES}
    return {**EN_UNITS, **EN_TENS, **EN_SCALES}
