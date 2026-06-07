"""Deterministic generator of labelled e-commerce extraction fixtures.

Builds >= 10,000 cases from templates x catalog x currencies x typo profiles.
Each case is a dict with the input text, language, and ground-truth labels used
by the measurement harness (``tests/test_fixture_corpus.py``).

Ground truth uses *canonical* head nouns (pre-typo), so the harness matches an
extracted product against the intended item with fuzzy tolerance.

Run as a script to (re)write the dataset:
    .venv/bin/python -m tests.fixtures.generator --count 12000 --out tests/fixtures/dataset.jsonl
"""

from __future__ import annotations

import argparse
import json
import random

from ector.dictionary.catalog import BRANDS, PRODUCT_NOUNS_EN, PRODUCT_NOUNS_FR
from tests.fixtures.typos import maybe_typo_phrase, typo_word

# Currency rendering: code -> list of surface spellings (clean).
CURRENCY_SURFACES = {
    "usd": ["usd", "dollars", "$", "bucks"],
    "eur": ["eur", "euros", "€"],
    "gbp": ["gbp", "pounds", "£", "quid"],
    "jpy": ["jpy", "yen", "¥"],
    "cad": ["cad"],
    "inr": ["inr", "rupees", "₹"],
}

# Adjectives to enrich product phrases (kept simple/non-essential to the head).
ADJ_EN = ["new", "cheap", "wireless", "portable", "small", "large", "black",
          "white", "red", "blue", "fast", "gaming", "smart", "premium"]
ADJ_FR = ["nouveau", "pas cher", "sans fil", "portable", "petit", "grand",
          "noir", "blanc", "rouge", "bleu", "rapide", "premium"]

# Sentence templates per language. {p} product, {q} quantity, {amt} amount,
# {cur} currency surface, {bud} budget amount.
TEMPLATES_EN_PRODUCT = [
    "I want a {p}",
    "I'm looking for a {p}",
    "do you have a {p}",
    "I need a {p}",
    "looking for {p}",
    "can you find me a {p}",
    "I'd like to buy a {p}",
    "is there a {p} available",
    "I want a {p} for {amt} {cur}",
    "looking for a {p} around {amt} {cur}",
    "I need a {p}, {amt} {cur} max",
    "do you sell {p} for {amt} {cur}",
    "I want {q} {p}",
    "I'd like {q} {p} please",
]
TEMPLATES_EN_MULTI = [
    "I want a {p1} and a {p2}",
    "I'm looking for a {p1} and {p2}",
    "I need a {p1}, a {p2} and a {p3}",
    "do you have a {p1} or a {p2}",
    "I want a {p1} for {amt} {cur} and a {p2}",
]
TEMPLATES_EN_BUDGET = [
    "my budget is {bud} {cur}",
    "I only have {bud} {cur}",
    "I can spend up to {bud} {cur}",
    "I have a budget of {bud} {cur}",
]

TEMPLATES_FR_PRODUCT = [
    "je veux un {p}",
    "je cherche un {p}",
    "est-ce que vous avez un {p}",
    "j'ai besoin d'un {p}",
    "je voudrais acheter un {p}",
    "je cherche un {p} pour {amt} {cur}",
    "je veux un {p} a {amt} {cur} max",
    "je voudrais {q} {p}",
]
TEMPLATES_FR_MULTI = [
    "je veux un {p1} et un {p2}",
    "je cherche un {p1} et un {p2}",
    "j'ai besoin d'un {p1}, d'un {p2} et d'un {p3}",
]
TEMPLATES_FR_BUDGET = [
    "mon budget est de {bud} {cur}",
    "je n'ai que {bud} {cur}",
    "j'ai un budget de {bud} {cur}",
]


def _products_for(lang: str) -> list[str]:
    base = PRODUCT_NOUNS_FR if lang == "fr" else PRODUCT_NOUNS_EN
    return [w for w in base if len(w) >= 4] + [b for b in BRANDS if len(b) >= 4]


def _adjs_for(lang: str) -> list[str]:
    return ADJ_FR if lang == "fr" else ADJ_EN


def _render_amount(rng: random.Random) -> tuple[str, float]:
    """Return (surface, value) for a price amount."""
    style = rng.random()
    if style < 0.5:
        v = rng.choice([5, 9, 10, 15, 20, 25, 30, 40, 50, 60, 75, 80, 99, 100,
                        120, 150, 199, 200, 250, 300, 500, 750, 1000])
        return str(v), float(v)
    if style < 0.7:
        v = round(rng.uniform(5, 500), 2)
        return f"{v:.2f}", float(v)
    if style < 0.85:
        v = rng.choice([1000, 1500, 2000, 1200, 2500])
        return f"{v:,}", float(v)  # thousands separator
    k = rng.choice([1, 2, 3, 5])
    return f"{k}k", float(k * 1000)


def _maybe_typo_currency(surface: str, rng: random.Random, profile: str) -> str:
    """Typo a currency surface only if it is an alphabetic word (not a symbol)."""
    if surface.isalpha() and len(surface) >= 4 and profile in ("single", "multi"):
        if rng.random() < 0.4:
            return typo_word(surface, rng, edits=1)
    return surface


PROFILES = ["clean", "single", "single", "multi", "keyboard", "transpose",
            "case", "spacing"]


def _gen_one(rng: random.Random, lang: str) -> dict:
    products = _products_for(lang)
    adjs = _adjs_for(lang)
    profile = rng.choice(PROFILES)

    kind = rng.random()
    case: dict = {"lang": lang, "profile": profile}

    def product_phrase() -> tuple[str, str]:
        head = rng.choice(products)
        if rng.random() < 0.4:
            adj = rng.choice(adjs)
            return f"{adj} {head}", head
        return head, head

    if kind < 0.5:
        # single product, maybe with price
        template = rng.choice(TEMPLATES_EN_PRODUCT if lang == "en" else TEMPLATES_FR_PRODUCT)
        phrase, head = product_phrase()
        expected_products = [head]
        fields: dict = {"p": phrase}
        expected_price = None
        expected_currency = None
        quantity = None
        if "{q}" in template:
            quantity = rng.choice([2, 3, 4, 5])
            fields["q"] = str(quantity)
        if "{amt}" in template:
            amt_surface, amt_value = _render_amount(rng)
            cur_code = rng.choice(list(CURRENCY_SURFACES))
            cur_surface = rng.choice(CURRENCY_SURFACES[cur_code])
            fields["amt"] = amt_surface
            fields["cur"] = _maybe_typo_currency(cur_surface, rng, profile)
            expected_price = amt_value
            expected_currency = cur_code
        text = template.format(**fields)
        case.update(
            text=_apply_profile(text, template, fields, rng, profile, lang),
            expected_products=expected_products,
            expected_price=expected_price,
            expected_currency=expected_currency,
            expected_quantity=quantity,
            expected_budget=None,
        )
    elif kind < 0.8:
        # multiple products
        template = rng.choice(TEMPLATES_EN_MULTI if lang == "en" else TEMPLATES_FR_MULTI)
        n = template.count("{p")
        heads = []
        fields = {}
        for i in range(1, n + 1):
            phrase, head = product_phrase()
            fields[f"p{i}"] = phrase
            heads.append(head)
        expected_price = None
        expected_currency = None
        if "{amt}" in template:
            amt_surface, amt_value = _render_amount(rng)
            cur_code = rng.choice(list(CURRENCY_SURFACES))
            cur_surface = rng.choice(CURRENCY_SURFACES[cur_code])
            fields["amt"] = amt_surface
            fields["cur"] = _maybe_typo_currency(cur_surface, rng, profile)
            expected_price = amt_value
            expected_currency = cur_code
        text = template.format(**fields)
        case.update(
            text=_apply_profile(text, template, fields, rng, profile, lang),
            expected_products=heads,
            expected_price=expected_price,
            expected_currency=expected_currency,
            expected_quantity=None,
            expected_budget=None,
        )
    else:
        # budget-only
        template = rng.choice(TEMPLATES_EN_BUDGET if lang == "en" else TEMPLATES_FR_BUDGET)
        bud_surface, bud_value = _render_amount(rng)
        cur_code = rng.choice(list(CURRENCY_SURFACES))
        cur_surface = rng.choice(CURRENCY_SURFACES[cur_code])
        fields = {"bud": bud_surface, "cur": _maybe_typo_currency(cur_surface, rng, profile)}
        text = template.format(**fields)
        case.update(
            text=_apply_profile(text, template, fields, rng, profile, lang),
            expected_products=[],
            expected_price=None,
            expected_currency=None,
            expected_quantity=None,
            expected_budget={"price": bud_value, "currency": cur_code},
        )
    return case


def _apply_profile(text, template, fields, rng, profile, lang) -> str:
    """Apply a typo profile to the non-numeric/non-currency words of ``text``.

    To keep labels valid we avoid typo-ing the amount digits; currency words may
    have been independently typo'd already. We apply word-level typo profiles to
    the whole sentence but protect tokens that are digits or contain symbols.
    """
    if profile in ("clean",):
        return text
    # Protect digit tokens by typo-ing only alphabetic words.
    words = text.split()
    protected = {w for w in words if any(ch.isdigit() for ch in w) or not w.isascii()}
    # Build a phrase of only typo-able words, apply profile, then stitch back.
    typoable = " ".join(w for w in words if w not in protected)
    if not typoable.strip():
        return text
    mutated = maybe_typo_phrase(typoable, rng, profile)
    mutated_words = mutated.split()
    out = []
    mi = 0
    for w in words:
        if w in protected:
            out.append(w)
        else:
            if mi < len(mutated_words):
                out.append(mutated_words[mi])
                mi += 1
            else:
                out.append(w)
    return " ".join(out)


def generate(count: int, seed: int = 1234) -> list[dict]:
    """Generate ``count`` labelled cases deterministically."""
    rng = random.Random(seed)
    cases = []
    for _ in range(count):
        lang = "en" if rng.random() < 0.7 else "fr"
        cases.append(_gen_one(rng, lang))
    return cases


def write_dataset(count: int, out_path: str, seed: int = 1234) -> int:
    cases = generate(count, seed)
    with open(out_path, "w", encoding="utf-8") as handle:
        for case in cases:
            handle.write(json.dumps(case, ensure_ascii=False) + "\n")
    return len(cases)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate ECTOR fixtures.")
    parser.add_argument("--count", type=int, default=12000)
    parser.add_argument("--seed", type=int, default=1234)
    parser.add_argument("--out", default="tests/fixtures/dataset.jsonl")
    args = parser.parse_args()
    n = write_dataset(args.count, args.out, args.seed)
    print(f"wrote {n} cases to {args.out}")


if __name__ == "__main__":
    main()
