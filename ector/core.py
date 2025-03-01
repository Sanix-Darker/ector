from typing import Any
import string
from ector.dictionary import (
    CURRENCY_MAP,
    CURRENCY_ONLY_PATTERN,
    EN_BUDGET_HINTS,
    FR_BUDGET_HINTS,
    FRENCH,
    MONEY_PATTERN,
)
from ector.triggers_fillers import (
    get_triggers_and_fillers,
    load_spacy_model,
    parse_money_entity,
)


async def contains_request_triggers(sentence: str, triggers: list[str]) -> bool:
    """
    Check if the sentence contains any of the given request trigger phrases or words.
    """
    low_text = sentence.lower()
    return any(trigger in low_text for trigger in triggers)


async def find_main_product_tokens(sentence) -> list:
    """
    Identify the main product-related tokens (NOUN or PROPN) within the given sentence.
    It looks for direct objects, prepositional objects, or subject complements in an existential construction.

    :param sentence: A spaCy Span object representing a sentence.
    :return: A list of spaCy Tokens representing the main product items.

    Examples:
        >>> import spacy
        >>> nlp = spacy.load("en_core_web_sm")
        >>> doc = nlp("I need a phone and a charger.")
        >>> product_tokens = find_main_product_tokens(doc.sents[0])
        >>> [token.text for token in product_tokens]
        ['phone', 'charger']
    """
    main_product_tokens = []

    for token in sentence:
        if token.pos_ not in ("NOUN", "PROPN"):
            continue

        # direct object (dobj, obj)
        if token.dep_ in ("dobj", "obj"):
            main_product_tokens.append(token)
        # prepositional object for "for"/"in" (en), "pour"/"dans" (fr), etc.
        elif (
            token.dep_ == "pobj"
            and token.head
            and token.head.lemma_.lower() in ("for", "in", "pour", "dans")
        ):
            main_product_tokens.append(token)
        # "price of"/"coût de" patterns
        elif (
            token.dep_ == "pobj"
            and token.head
            and token.head.lemma_.lower() in ("of", "de")
        ):
            if token.head.head and token.head.head.lemma_.lower() in (
                "price",
                "coût",
                "coûter",
            ):
                main_product_tokens.append(token)
        # subject complement with existential 'il y a' or 'there is'
        elif (
            token.dep_ == "attr"
            and token.head
            and token.head.lemma_.lower() in ("être", "be")
        ):
            # check for "il" or "there" as an expletive
            if any(
                child.lower_ in ("il", "there")
                for child in token.head.children
                if child.dep_ == "expl"
            ):
                main_product_tokens.append(token)

    # Also include conjuncts (e.g., "a phone and a charger")
    for t in list(main_product_tokens):
        for conj in t.conjuncts:
            if conj.pos_ in ("NOUN", "PROPN"):
                main_product_tokens.append(conj)

    # remove duplicates and sort by token index in the sentence
    main_product_tokens = sorted(set(main_product_tokens), key=lambda t: t.i)
    return main_product_tokens


def collect_product_phrase(product_token, main_product_tokens: list):
    """
    Recursively collect tokens (including modifiers/children) for a given product token
    to build a descriptive phrase while avoiding overlap with other main product tokens.

    :param product_token: The spaCy Token representing the main product item.
    :param main_product_tokens: A list of main product tokens in the sentence.
    :return: A string containing the descriptive phrase (untrimmed, uncleaned).

    Examples:
        >>> # Suppose we have a sentence "I want a big red apple and a small green pear."
        >>> # We have tokens 'apple' and 'pear' as main_product_tokens
        >>> # This function for 'apple' would collect "big red apple".
    """
    words = []

    def collect_descendants(tok):
        for child in tok.children:
            # skip coordinating conjunctions, punctuation
            if child.dep_ in ("conj", "cc", "punct"):
                continue
            # if this child is also a separate main product, skip it
            if child in main_product_tokens:
                continue
            words.append(child)
            collect_descendants(child)

    # start with the product token itself
    words.append(product_token)
    collect_descendants(product_token)

    # sort by token index to maintain natural word order
    words = sorted(set(words), key=lambda t: t.i)
    phrase = " ".join([w.text for w in words]).strip()
    return phrase


def clean_phrase(phrase: str, filler_phrases: list[str]) -> str:
    """
    Remove leading filler phrases and articles from the phrase, and trim punctuation.

    :param phrase: A descriptive phrase extracted from the sentence.
    :param filler_phrases: A list of known filler phrases (e.g. "i need", "je cherche") to remove.
    :return: A cleaned-up version of the phrase with capitalized first letter.

    Examples:
        >>> fill_en = ["i need", "i want", "please"]
        >>> phrase = "i need a big red apple."
        >>> clean_phrase(phrase, fill_en)
        'Big red apple'
    """
    lower_phrase = phrase.lower()

    # remove filler phrases
    for fp in filler_phrases:
        if not lower_phrase.startswith(fp + " "):
            continue
        phrase = phrase[len(fp) :].strip()
        lower_phrase = phrase.lower()

    # remove articles (English/French)
    articles = ["a ", "an ", "the ", "un ", "une ", "le ", "la ", "les "]
    for article in articles:
        if not lower_phrase.startswith(article):
            continue
        phrase = phrase[len(article) :].strip()
        lower_phrase = phrase.lower()

    # remove leading/trailing punctuation
    phrase = phrase.strip(".,!?;:").strip()

    # capitalize if not empty
    if phrase:
        return phrase[0].upper() + phrase[1:]

    return phrase


def extract_price_info_from_sentence(sentence) -> tuple[Any, Any]:
    """
    Look for MONEY entities in the sentence and parse out (price, currency).
    Returns the first found or (None, None) if none found.
    """
    for ent in sentence.ents:
        if ent.label_ != "MONEY":
            continue

        price_, currency_ = parse_money_entity(ent.text)
        if price_:
            return price_, currency_

    return None, None


async def maybe_budget(sentence_text: str, lang: str = "en") -> bool:
    """
    Heuristic check to see if a user might be indicating a budget,
    using extensive lists of hints for English and French.

    :param sentence_text: A single sentence from user input.
    :param lang: Either 'en' or 'fr' (extend for more languages as needed).
    :return: True if the sentence likely references a budget, False otherwise.
    """
    text_lower = sentence_text.lower()

    # If the word "budget" itself appears anywhere, consider it a budget reference
    if "budget" in text_lower:
        return True

    if lang == FRENCH:
        return any(hint in text_lower for hint in FR_BUDGET_HINTS)

    return any(hint in text_lower for hint in EN_BUDGET_HINTS)


async def extract_price_info(sentence_text: str):
    """
    Parse the first occurrence of a numeric + currency pattern from the raw sentence text.
    Returns (price, currency) or (None, None) if no match.

    Examples:
        >>> extract_price_info("It costs 100 USD.")
        (100.0, 'usd')
        >>> extract_price_info("I have 200 CAD")
        (200.0, 'cad')
        >>> extract_price_info("That is 300 yen.")
        (300.0, 'jpy')
        >>> extract_price_info("No price here")
        (None, None)
        >>> extract_price_info("It's 25$")
        (25.0, 'usd')
        >>> extract_price_info("It costs 500 Rupees")
        (500.0, 'inr')
    """
    match = MONEY_PATTERN.search(sentence_text)
    if match:
        amount_str = match.group(1)
        currency_str = (match.group(2) or "").strip().lower()

        # Map to standard currency code if possible
        if currency_str in CURRENCY_MAP:
            currency_str = CURRENCY_MAP[currency_str]
        elif currency_str == "":
            currency_str = None  # e.g. user typed "It costs 100"
        return float(amount_str), currency_str
    return None, None


async def add_product(product_name, price, currency, products):
    """Just adding product to the list of products to be returned"""

    if CURRENCY_ONLY_PATTERN.search(product_name):
        return

    entry = {"product": product_name}
    if price is not None and price > 0:
        entry["price"] = price

    if currency is not None:
        entry["currency"] = currency
    products.append(entry)


def replace_punctuation_with_fullstop(text: str) -> str:
    result_chars = []
    for ch in text:
        if ch in string.punctuation:
            result_chars.append(".")
            continue
        result_chars.append(ch)
    return "".join(result_chars)


async def extract(text: str, lang: str = "en") -> dict:
    """
    Asynchronously extract product requests and an inferred budget from the input text.
    If a sentence contains a recognized product request trigger, it's treated as a product request.
    If a sentence lacks triggers or product tokens but includes a price with phrases like "only have",
    it is treated as a budget. This avoids interpreting a standalone price as a product.

    Returns:
        {
            "product_requests": [
                {
                    "product": <str>,
                    "price": <float or None>,
                    "currency": <str or None>
                }, ...
            ],
            "budget": {
                "price": <float>,
                "currency": <str>
            }
        }
        (budget only appears if inferred)
    """
    text = replace_punctuation_with_fullstop(text)
    nlp = load_spacy_model(lang)
    request_triggers, filler_phrases = get_triggers_and_fillers(lang)
    doc = nlp(text)

    products = []
    budget_info = {"price": 0.0, "currency": None}

    for sent in doc.sents:
        sentence_text = sent.text.strip()
        if not sentence_text:
            continue

        found_price, found_currency = await extract_price_info(sentence_text)
        has_triggers = await contains_request_triggers(sentence_text, request_triggers)
        main_product_tokens = await find_main_product_tokens(sent)

        # 1) If no triggers or products, but text suggests a budget, treat as budget
        if not has_triggers and not main_product_tokens and found_price is not None:
            if not await maybe_budget(sentence_text):
                continue
            budget_info["price"] = found_price
            budget_info["currency"] = found_currency

        # 2) If the sentence explicitly indicates budget, store it and skip product extraction
        if await maybe_budget(sentence_text) and found_price is not None:
            budget_info["price"] = found_price
            budget_info["currency"] = found_currency
            continue

        # 3) If sentence has triggers, treat it as product request context
        if has_triggers:
            # No product tokens, but there's a price -> minimal product request
            if not main_product_tokens:
                if found_price is None:
                    continue
                await add_product(None, found_price, found_currency, products)

            # We have product tokens
            for token in main_product_tokens:
                raw_phrase = collect_product_phrase(token, main_product_tokens)
                cleaned_product = clean_phrase(raw_phrase, filler_phrases)
                if cleaned_product and "budget" not in cleaned_product.lower():
                    await add_product(
                        cleaned_product, found_price, found_currency, products
                    )

        # 4) No triggers but product tokens exist -> treat as normal requests
        elif main_product_tokens:
            for token in main_product_tokens:
                raw_phrase = collect_product_phrase(token, main_product_tokens)
                cleaned_product = clean_phrase(raw_phrase, filler_phrases)
                if cleaned_product and "budget" not in cleaned_product.lower():
                    await add_product(
                        cleaned_product, found_price, found_currency, products
                    )

    # Build final output
    if budget_info["price"] and budget_info["price"] > 0 and budget_info["currency"]:
        return {"products": products, "budget": budget_info}

    return {"products": products}
