"""Public extraction orchestration.

Thin coordinator that wires together the focused modules (money, products,
budget, triggers, languages, models, text_utils). The heavy lifting is
synchronous (``extract_sync``); the historical ``extract`` coroutine simply wraps
it so existing ``asyncio.run(extract(...))`` callers keep working (SMELL-001,
D-06-1).

Result schema (normative, see docs/features/06-public-api.md)::

    {
        "products": [
            {"product": <str>, "price": <float>?, "currency": <str>?, "quantity": <int>?},
            ...
        ],
        "budget": {"price": <float>, "currency": <str>?}   # only if inferred
    }
"""

from __future__ import annotations

from ector.attributes import detect_attributes, detect_brand, detect_condition
from ector.budget import build_budget, is_budget
from ector.constraints import parse_constraint
from ector.intent import classify_intent
from ector.languages import get_language
from ector.models import get_model
from ector.money import is_currency_only, normalize_currency, parse_price
from ector.normalize import normalize_vocabulary
from ector.products import (
    collect_product_phrase,
    detect_quantity,
    extract_products_fallback,
    find_main_product_tokens,
    find_preposition_price,
    product_spec_text,
)
from ector.text_utils import clean_phrase, normalize_text
from ector.triggers import contains_trigger
from ector.types import ExtractResult, Product


def _make_product(
    name: str,
    price: float | None,
    currency: str | None,
    quantity: int | None,
    lang: str = "en",
    condition: str | None = None,
    attr_source: str | None = None,
) -> Product | None:
    """Build a product entry, or ``None`` if the name is empty/currency-only.

    A product must have a non-empty, non-currency-only name (matching the
    documented schema). Nameless price-only requests (a trigger + price but no
    product noun, e.g. "I want to buy for 50 usd") carry no product and are
    skipped rather than emitting ``{"product": null}``. The phrase is enriched
    with brand / attributes / condition when detected (additive fields). A
    sentence-level ``condition`` may be supplied; ``attr_source`` (e.g. the
    product's parse subtree text) is used for attribute detection in addition to
    the name, so specs like "4k HD" attached via prepositions are captured.
    """
    if not name or is_currency_only(name) or "budget" in name.lower():
        return None
    product: Product = {"product": name}
    if price is not None and price > 0:
        product["price"] = price
    if currency is not None:
        product["currency"] = currency
    if quantity is not None:
        product["quantity"] = quantity

    brand = detect_brand(name)
    if brand is not None:
        product["brand"] = brand
    attributes = detect_attributes(attr_source or name, lang)
    if attributes:
        product["attributes"] = attributes
    cond = detect_condition(attr_source or name, lang) or condition
    if cond is not None:
        product["condition"] = cond
    return product


def _head_word(name: str) -> str:
    """Return a normalized head word (last token) of a product name for dedupe."""
    tokens = name.lower().split()
    return tokens[-1] if tokens else name.lower()


def _sentence_price(
    sentence_text: str, sentence, config
) -> tuple[float | None, str | None]:
    """Resolve a price for a sentence.

    First a currency-qualified amount (e.g. "200 usd", "$25"); otherwise a number
    that is the object of a price preposition ("for 250"). Bare quantities like
    "2 phones" are intentionally not treated as prices (BUG-010).
    """
    price, currency = parse_price(sentence_text, lang=config.code)
    if price is not None:
        return price, currency
    prep_price = find_preposition_price(sentence, config)
    return prep_price, None


def _budget_from_text(text: str, lang: str):
    """Resolve a budget (price + possibly-fuzzy currency) from budget text."""
    price, currency = parse_price(text, allow_bare=True, lang=lang)
    if price is None:
        return None
    if currency is None:
        currency = _fuzzy_currency_in(text)
    return build_budget(price, currency)


def _fuzzy_currency_in(text: str):
    """Find a currency in ``text`` allowing a misspelled currency word."""
    import re as _re

    for word in _re.findall(r"[^\W\d_]+", text):
        if len(word) < 3:
            continue
        code = normalize_currency(word)
        if code is not None:
            return code
    return None


def _classify_sentence(sent, config):
    """Build a record describing one sentence's signals."""
    sentence_text = sent.text.strip()
    price, currency = _sentence_price(sentence_text, sent, config)
    return {
        "span": sent,
        "text": sentence_text,
        "price": price,
        "currency": currency,
        "has_trigger": contains_trigger(sentence_text, config),
        "product_tokens": find_main_product_tokens(sent, config),
        "is_budget": is_budget(sentence_text, config),
    }


def _build_products_for_sentence(rec, config, price, currency) -> list[Product]:
    """Build product entries for one sentence record using the given price."""
    out: list[Product] = []
    product_tokens = rec["product_tokens"]
    lang = config.code
    # Sentence-level condition (e.g. "refurbished", "d'occasion") applies to
    # products in this clause when their own name does not carry one.
    sent_condition = detect_condition(rec["text"], lang)

    if not product_tokens:
        for item in extract_products_fallback(rec["span"], config):
            name = clean_phrase(item["name"], config.fillers)
            entry = _make_product(name, price, currency, item["quantity"], lang, sent_condition)
            if entry is not None:
                out.append(entry)
        return out

    captured_heads: set[str] = set()
    for token in product_tokens:
        raw_phrase = collect_product_phrase(token, product_tokens)
        name = clean_phrase(raw_phrase, config.fillers)
        quantity = detect_quantity(token)
        spec = product_spec_text(token, product_tokens)
        entry = _make_product(name, price, currency, quantity, lang, sent_condition, spec)
        if entry is not None:
            out.append(entry)
            captured_heads.add(_head_word(entry["product"]))

    for item in extract_products_fallback(rec["span"], config):
        name = clean_phrase(item["name"], config.fillers)
        if not name or _head_word(name) in captured_heads:
            continue
        entry = _make_product(name, price, currency, item["quantity"], lang, sent_condition)
        if entry is not None:
            out.append(entry)
            captured_heads.add(_head_word(name))
    return out


def extract_sync(text: str, lang: str = "en") -> ExtractResult:
    """Synchronously extract products and an optional budget from ``text``."""
    # Fast path: empty/whitespace input needs no model work.
    if not text or not text.strip():
        return {"products": [], "intent": "browse"}

    config = get_language(lang)
    nlp = get_model(config.model_name)

    # Typo-correct closed-class / known vocabulary, then segment.
    corrected = normalize_vocabulary(text, config.code)
    normalized = normalize_text(corrected)
    doc = nlp(normalized)

    records = [
        _classify_sentence(sent, config)
        for sent in doc.sents
        if sent.text.strip()
    ]

    # Price-tail reconciliation: a clause that has a price but no product and is
    # Reconciliation across comma/sentence splits. A "price tail" is a clause
    # that carries a price but no product, trigger, or budget keyword (e.g.
    # "..., 304 cad max", or just "20 £" split off from "je n'ai que").
    for i, rec in enumerate(records):
        is_price_tail = (
            rec["price"] is not None
            and not rec["product_tokens"]
            and not rec["has_trigger"]
            and not rec["is_budget"]
        )
        if not is_price_tail or i == 0:
            continue
        prev = records[i - 1]
        # (a) previous clause is a budget keyword without a price -> form budget
        if prev["is_budget"] and prev["price"] is None:
            prev["price"] = rec["price"]
            prev["currency"] = rec["currency"]
            rec["consumed"] = True
        # (b) previous clause has products/trigger but no price -> lend price
        elif prev["price"] is None and (prev["product_tokens"] or prev["has_trigger"]):
            prev["price"] = rec["price"]
            prev["currency"] = rec["currency"]
            rec["consumed"] = True

    products: list[Product] = []
    budget = None

    for idx, rec in enumerate(records):
        if rec.get("consumed"):
            continue

        # Budget sentence with a price -> record budget, skip products.
        if rec["is_budget"]:
            # Prefer a reconciled price (from a split-off tail clause); else
            # parse the budget text directly, and if that fails, parse the budget
            # text joined with the next clause (spaCy sometimes splits an amount
            # and its currency, e.g. "budget de 9" + "usd").
            if rec["price"] is not None:
                new_budget = build_budget(rec["price"], rec["currency"])
            else:
                new_budget = _budget_from_text(rec["text"], config.code)
                if new_budget is None and idx + 1 < len(records):
                    joined = rec["text"] + " " + records[idx + 1]["text"]
                    new_budget = _budget_from_text(joined, config.code)
                    if new_budget is not None and not records[idx + 1]["product_tokens"]:
                        records[idx + 1]["consumed"] = True
            if new_budget is not None:
                budget = new_budget
                # A budget sentence may still mention a product ("budget 200 for
                # a laptop"); only skip if it has no product signal.
                if not rec["product_tokens"]:
                    fb = _build_products_for_sentence(rec, config, None, None)
                    if not fb:
                        continue

        # Build products for this sentence (dependency + token fallback). The
        # fallback runs even without an explicit trigger so content-only clauses
        # (e.g. a comma-split tail like "d'un batterie et google") are captured.
        sentence_products = _build_products_for_sentence(
            rec, config, rec["price"], rec["currency"]
        )
        if not rec["is_budget"]:
            products.extend(sentence_products)
        elif rec["product_tokens"]:
            # budget sentence that also names a product
            products.extend(sentence_products)

    result: ExtractResult = {"products": products}
    if budget is not None:
        result["budget"] = budget

    # Price constraint (max/min/around/between) parsed from the corrected text.
    constraint = parse_constraint(normalized)
    if constraint is not None:
        result["price_constraint"] = constraint

    # Coarse intent classification.
    result["intent"] = classify_intent(normalized, has_products=bool(products))

    return result


async def extract(text: str, lang: str = "en") -> ExtractResult:
    """Asynchronously extract products and an optional budget from ``text``.

    Backwards-compatible coroutine wrapper around :func:`extract_sync` so existing
    ``asyncio.run(extract(...))`` usage keeps working. No real I/O is awaited.
    """
    return extract_sync(text, lang)
