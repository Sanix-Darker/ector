"""Baseline diagnostics: empirically confirm the bugs catalogued in docs/audit.

Run:  .venv/bin/python scripts/diagnose_baseline.py
This script does NOT modify anything; it only prints observed behavior.
"""
import asyncio
import json

from ector import extract
from ector.dictionary import FILLER_PHRASES_EN, FILLER_PHRASES_FR


def show(title, value):
    print(f"\n=== {title} ===")
    print(value)


def main():
    # BUG-004: missing-comma concatenation in filler lists
    bad_en = [p for p in FILLER_PHRASES_EN if "somesome" in p]
    bad_fr = [p for p in FILLER_PHRASES_FR if "desje" in p or "achatj" in p]
    show("BUG-004 EN concatenated entries", bad_en)
    show("BUG-004 FR concatenated entries", bad_fr)

    # BUG-009 (resolved): word-boundary trigger matching. Raw substring would
    # match 'get' in 'forget'; contains_trigger must not.
    from ector.languages import get_language
    from ector.triggers import contains_trigger

    en = get_language("en")
    show(
        "BUG-009 raw substring 'get' in 'forget'",
        "get" in "i will forget the milk".lower(),
    )
    show(
        "BUG-009 contains_trigger('i will forget the milk')",
        contains_trigger("i will forget the milk", en),
    )

    # BUG-010: bare number parsed as price (quantity confusion)
    show(
        "BUG-010 quantity-as-price 'I want 2 phones'",
        json.dumps(asyncio.run(extract("I want 2 phones.")), indent=2),
    )

    # BUG-008: currency-less budget dropped
    show(
        "BUG-008 'my budget is 300' (no currency)",
        json.dumps(asyncio.run(extract("My budget is 300.")), indent=2),
    )

    # BUG-001: French budget hint without literal 'budget' word
    show(
        "BUG-001 FR 'je n'ai que 50 euros' (no 'budget' word)",
        json.dumps(asyncio.run(extract("je n'ai que 50 euros.", "fr")), indent=2),
    )

    # RISK-009: 'pound cake' dropped by CURRENCY_ONLY_PATTERN substring
    show(
        "RISK-009 'I want a pound cake'",
        json.dumps(asyncio.run(extract("I want a pound cake.")), indent=2),
    )

    # BUG-002 (resolved): money parsing now lives in ector.money and returns floats.
    from ector.money import parse_price

    price, currency = parse_price("9 eur")
    show("BUG-002 parse_price type", f"{price!r} ({type(price).__name__}), {currency!r}")


if __name__ == "__main__":
    main()
