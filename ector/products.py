"""Product token discovery, phrase building, and quantity detection.

Synchronous (no fake async - SMELL-001). Uses per-language dependency/lemma hints
from :class:`ector.languages.LanguageConfig` instead of hardcoded English
assumptions (RISK-005). Quantities (e.g. "2 phones") are detected and kept out of
both the product name and the price (BUG-010).

See ``docs/features/01-product-extraction.md``.
"""

from __future__ import annotations

import re
from functools import lru_cache

from spacy.tokens import Span, Token

from ector.dictionary.attributes import RESOLUTIONS, all_attribute_words
from ector.dictionary.catalog import catalog_terms_for
from ector.fuzzy import FuzzyIndex, threshold_for
from ector.languages import LanguageConfig
from ector.money import is_currency_only

# Resolution/spec tokens (may contain digits) that are attributes, not amounts.
_RESOLUTION_RE = re.compile(r"^(?:\d{1,4}k|\d{3,4}p|full-?hd)$", re.IGNORECASE)


def _is_resolution(word: str) -> bool:
    w = word.lower()
    return w in RESOLUTIONS or _RESOLUTION_RE.match(w) is not None

# Fuzzy catalog indexes per language, built lazily.
_CATALOG_INDEXES: dict[str, FuzzyIndex] = {}
_ATTRIBUTE_INDEXES: dict[str, FuzzyIndex] = {}


def _catalog_index(lang: str) -> FuzzyIndex:
    idx = _CATALOG_INDEXES.get(lang)
    if idx is None:
        idx = FuzzyIndex(catalog_terms_for(lang))
        _CATALOG_INDEXES[lang] = idx
    return idx


def _attribute_index(lang: str) -> FuzzyIndex:
    idx = _ATTRIBUTE_INDEXES.get(lang)
    if idx is None:
        idx = FuzzyIndex(all_attribute_words(lang))
        _ATTRIBUTE_INDEXES[lang] = idx
    return idx


def _matches_catalog(word: str, config: LanguageConfig) -> bool:
    """True if ``word`` is (a close typo of) a known catalog product/brand."""
    if len(word) < 3:
        return False
    return _catalog_index(config.code).best_match(word, threshold_for(word)) is not None


def _is_attribute_word(word: str, config: LanguageConfig) -> bool:
    """True if ``word`` is (a close typo of) a known attribute/descriptor."""
    if len(word) < 3:
        return word in all_attribute_words(config.code)
    return _attribute_index(config.code).best_match(word, threshold_for(word)) is not None

# Dependency labels that introduce a descriptive modifier worth keeping in the
# product phrase (adjectives, compound nouns, noun modifiers, flat names).
_MODIFIER_DEPS = frozenset({"amod", "compound", "nmod", "flat", "fixed", "poss"})

# Modifier surface forms to drop from a product phrase: constraint/comparison
# words, currency words, and greetings. These otherwise bloat names like
# "Ordinateur portable occasion euros" / "Televiseur 400".
# NOTE: condition adjectives ("new"/"neuf"/"used") are intentionally KEPT in the
# name (they are descriptive); condition is also surfaced as a separate field.
_PHRASE_STOP_MODIFIERS = frozenset({
    # condition expressed as a noun ("d'occasion", "reconditionné") - the
    # condition is surfaced separately; keep adjectives like "neuf"/"new".
    "occasion", "reconditionne", "reconditionné", "refurbished",
    # constraint / comparison
    "max", "maximum", "min", "minimum", "moins", "plus", "environ", "entre",
    "under", "over", "around", "about", "between", "least", "most",
    # currency words (also caught by is_currency_only, kept for clarity)
    "euros", "euro", "dollars", "dollar", "usd", "eur", "gbp",
    # greetings / politeness
    "bonjour", "salut", "hello", "hi", "merci", "please", "svp",
    # misc
    "total", "totale",
})

# Dependency labels for the head being a direct/prepositional object.
_OBJECT_DEPS = frozenset({"dobj", "obj"})

# Shorthand amount like "5k", "1k", "2k" that should never be a product.
_SHORTHAND_AMOUNT = re.compile(r"\d+(?:[.,]\d+)?k", re.IGNORECASE)


# Words/lemmas that are never products even when they appear as a grammatical
# object (e.g. French "besoin" = need, English "need"/"thing").
_NON_PRODUCT_LEMMAS = frozenset({
    "besoin", "need", "want", "wish", "envie", "intention", "thing", "things",
    "chose", "choses", "item", "items", "article", "articles", "produit",
    "produits", "product", "products", "budget", "price", "prix", "tarif",
    "cost", "costs", "deal", "deals", "offer", "offers", "stock", "order",
    "commande", "devis", "quote", "option", "options", "truc", "trucs",
    # contraction / elision fragments produced by tokenizers on typo'd input
    "i'd", "i'm", "i've", "i'll", "j'", "j''ai", "jai", "ja'", "n'", "n'ai",
    "qu'", "que", "qu", "d'", "l'", "c'", "s'", "t'", "m'", "fil", "est-ce",
    "ce", "vous", "nous", "aai", "wvez", "yvous", "u", "ur", "hav", "hl",
    # constraint / comparison / question words that are not products
    "much", "many", "under", "over", "above", "below", "less", "more", "most",
    "least", "around", "about", "approximately", "between", "max", "maximum",
    "min", "minimum", "moins", "plus", "environ", "entre", "autour", "maxi",
    "mini", "combien", "how", "what", "comment", "quel", "quelle",
    # greetings / politeness (never products)
    "bonjour", "salut", "hello", "hi", "hey", "merci", "please", "svp",
    "coucou", "bonsoir",
})


def _is_excluded_word(token: Token) -> bool:
    """True if the token is a known non-product word (by text or lemma)."""
    return token.lower_ in _NON_PRODUCT_LEMMAS or token.lemma_.lower() in _NON_PRODUCT_LEMMAS


def _is_product_noun(token: Token) -> bool:
    """A candidate product token must be a noun-like word, not a number/currency."""
    if token.pos_ not in ("NOUN", "PROPN"):
        return False
    if token.like_num:
        return False
    if is_currency_only(token.text):
        return False
    if _is_excluded_word(token):
        return False
    return True


def _is_object_candidate(token: Token) -> bool:
    """Accept a verb object as a product even if the model mis-tags it.

    Some inputs are mis-tagged by the statistical model (e.g. the French model
    tags "iPhone" in "je veux un iPhone noir" as ADJ rather than PROPN). When a
    token is the direct object of a verb we still treat it as a product as long
    as it is not a pronoun, number, or currency token (RISK-005).
    """
    if token.pos_ in ("PRON", "NUM", "DET", "ADP", "PUNCT", "SYM", "VERB", "AUX"):
        return False
    if token.like_num:
        return False
    if is_currency_only(token.text):
        return False
    if _is_excluded_word(token):
        return False
    return True


def _subtree_is_money_phrase(token: Token) -> bool:
    """True if the token's subtree looks like a price phrase (has currency/number).

    Used to reject candidates such as "max" in "at 150 usd max", whose subtree
    contains a currency token ("usd") and a number ("150"); that is a price, not
    a product.
    """
    for descendant in token.subtree:
        if descendant is token:
            continue
        if descendant.like_num or is_currency_only(descendant.text):
            return True
    return False


def find_main_product_tokens(sentence: Span, config: LanguageConfig) -> list[Token]:
    """Identify the main product tokens (NOUN/PROPN) within a sentence.

    Looks for direct objects, prepositional objects of product-introducing
    prepositions, "price of" patterns, and existential subject complements, then
    adds conjuncts. Currency tokens and bare numbers are excluded so price
    fragments are never mistaken for products.

    :param sentence: a spaCy ``Span`` (one sentence).
    :param config: the active :class:`LanguageConfig`.
    :return: product tokens sorted by position.

    Example:
        >>> import spacy
        >>> from ector.languages import get_language
        >>> nlp = spacy.load("en_core_web_sm")  # doctest: +SKIP
        >>> doc = nlp("I need a phone and a charger.")  # doctest: +SKIP
        >>> sent = next(doc.sents)  # doctest: +SKIP
        >>> [t.text for t in find_main_product_tokens(sent, get_language("en"))]  # doctest: +SKIP
        ['phone', 'charger']
    """
    main_tokens: list[Token] = []

    for token in sentence:
        head = token.head
        head_lemma = head.lemma_.lower() if head is not None else ""

        # direct object - accept even mildly mis-tagged objects (RISK-005)
        if token.dep_ in _OBJECT_DEPS:
            if _is_object_candidate(token):
                main_tokens.append(token)
            continue

        # remaining branches require a genuine noun/propn
        if not _is_product_noun(token):
            continue

        # prepositional object of a product-introducing preposition
        if token.dep_ == "pobj" and head_lemma in config.price_prepositions | {
            "in",
            "dans",
        }:
            # Skip money phrases like "at 150 usd max" (subtree has currency/num).
            if not _subtree_is_money_phrase(token):
                main_tokens.append(token)
        # "price of" / "coût de" patterns
        elif token.dep_ == "pobj" and head_lemma in ("of", "de"):
            grand = head.head if head is not None else None
            if grand is not None and grand.lemma_.lower() in ("price", "coût", "coûter"):
                main_tokens.append(token)
        # existential subject complement: "there is X" / "il y a X"
        elif token.dep_ == "attr" and head_lemma in config.copula_lemmas:
            if any(
                child.lower_ in config.expletives
                for child in head.children
                if child.dep_ == "expl"
            ):
                main_tokens.append(token)

    # include conjuncts (e.g. "a phone and a charger")
    for token in list(main_tokens):
        for conj in token.conjuncts:
            if _is_object_candidate(conj):
                main_tokens.append(conj)

    # Recover product nouns conjoined across a price phrase, e.g.
    # "a keyboard for 40 usd and a monitor" where the model attaches "monitor"
    # as a conjunct of the currency token. A conj noun that carries its own
    # determiner ("a monitor") is a strong product signal.
    existing = set(main_tokens)
    for token in sentence:
        if token in existing:
            continue
        if token.dep_ != "conj" or not _is_product_noun(token):
            continue
        if _subtree_is_money_phrase(token):
            continue
        if any(child.dep_ == "det" for child in token.children):
            main_tokens.append(token)

    # Drop attribute/descriptor tokens (colors, "premium", "wireless", "noir",
    # "rapide", ...) that were picked up as standalone product heads. They are
    # modifiers, not products. Catalog products that happen to be attribute-like
    # (e.g. FR "portable") are kept.
    filtered = [
        t for t in main_tokens
        if _matches_catalog(t.lower_, config) or not _is_attribute_word(t.lower_, config)
    ]
    # Never return an empty list solely due to this filter when we had tokens.
    if not filtered and main_tokens:
        filtered = main_tokens

    # dedupe + order by position
    return sorted(set(filtered), key=lambda t: t.i)


def detect_quantity(product_token: Token) -> int | None:
    """Return the integer quantity modifying a product token, if any.

    Detects a ``nummod`` numeric child (e.g. the "2" in "2 phones"). Returns
    ``None`` when there is no integer quantity. This keeps quantities out of the
    price (BUG-010).
    """
    for child in product_token.children:
        if child.dep_ == "nummod" and child.like_num:
            try:
                value = float(child.text)
            except ValueError:
                continue
            if value.is_integer():
                return int(value)
    return None


def collect_product_phrase(
    product_token: Token, main_product_tokens: list[Token]
) -> str:
    """Build a descriptive phrase for a product token from its modifiers.

    Includes only descriptive modifiers (adjectives, compounds, noun modifiers)
    recursively, excluding determiners, prepositions, conjunctions, punctuation,
    numeric quantities, and other main product tokens. This avoids dragging in
    price prepositions like "for 200 usd" (the old code produced "Smartphone for").

    :return: the raw phrase (uncleaned); pass through ``text_utils.clean_phrase``.
    """
    others = set(main_product_tokens)
    words: list[Token] = [product_token]

    def _keep_modifier(child: Token) -> bool:
        # Drop raw numbers so they never bloat the product name ("Televiseur 400").
        if child.like_num:
            return False
        # US-003 / RISK-009: a currency word whose subtree also carries a
        # numeric amount is a price fragment ("usd" in "200 usd") and must
        # be dropped; a currency word with NO numeric in its subtree is a
        # descriptive compound-noun modifier ("pound" in "pound cake") and
        # is KEPT.
        if is_currency_only(child.lower_) and any(n.like_num for n in child.subtree):
            return False
        # Drop condition/constraint/elision surface forms ("Ordinateur portable
        # occasion euros", "minimum" / "max").
        if child.lower_ in _PHRASE_STOP_MODIFIERS:
            return False
        return True

    def collect(tok: Token) -> None:
        for child in tok.children:
            if child in others:
                continue
            if child.dep_ not in _MODIFIER_DEPS:
                continue
            if child.dep_ == "nummod":  # quantity handled separately
                continue
            if not _keep_modifier(child):
                continue
            words.append(child)
            collect(child)

    collect(product_token)
    ordered = sorted(set(words), key=lambda t: t.i)
    return " ".join(w.text for w in ordered).strip()


def product_spec_text(product_token: Token, main_product_tokens: list[Token]) -> str:
    """Return the product token's subtree text, excluding other products and the
    currency/number parts of any price phrase.

    Used to detect attributes/specs that hang off the product via prepositions
    (e.g. "monitor with 4k HD"), which ``collect_product_phrase`` deliberately
    omits from the display name. We stop descending into a subtree that is a
    money phrase so prices like "for 200 usd" never become attributes.
    """
    others = set(main_product_tokens)
    keep: list[Token] = [product_token]

    def walk(tok: Token) -> None:
        for child in tok.children:
            if child in others:
                continue
            if child.dep_ in ("cc", "conj", "punct"):
                continue
            # skip price prepositions / money subtrees and bare currency/amounts
            if _subtree_is_money_phrase(child) or is_currency_only(child.lower_):
                continue
            keep.append(child)
            walk(child)

    walk(product_token)
    ordered = sorted(set(keep), key=lambda t: t.i)
    return " ".join(t.text for t in ordered).strip()


def find_preposition_price(sentence: Span, config: LanguageConfig) -> float | None:
    """Find a bare number that is the object of a price preposition.

    Covers "a phone for 250" where 250 is a price even without a currency token.
    Returns the numeric value or ``None``.
    """
    for token in sentence:
        if not token.like_num:
            continue
        head = token.head
        if head is None:
            continue
        if token.dep_ in ("pobj", "obj", "nummod") and head.lemma_.lower() in config.price_prepositions:
            try:
                return float(token.text)
            except ValueError:
                continue
    return None


# ---------------------------------------------------------------------------
# Token-based fallback extractor (parse-independent) - Feature 08, Layer 2.
# ---------------------------------------------------------------------------

# Generic words that are never products on their own. Kept minimal; the bulk of
# filtering comes from triggers/fillers/budget-hints/currencies/numbers.
_STOP_POS = frozenset({"DET", "ADP", "CCONJ", "SCONJ", "PRON", "AUX", "PART",
                       "PUNCT", "SPACE", "NUM", "SYM", "INTJ"})

# Connector surface forms that split product groups.
_GROUP_SPLITTERS = frozenset({"and", "et", "or", "ou", "plus", "with", "avec",
                              "&", ",", ";", "also", "aussi", "then", "puis"})

# Verbs/words that are clearly not products even if tagged as nouns by a model
# confused by typos. Built from the language's trigger single-words.
_GENERIC_NON_PRODUCT = frozenset({
    "budget", "price", "prices", "cost", "costs", "deal", "deals", "sale",
    "discount", "offer", "offers", "promotion", "promo", "stock", "order",
    "quote", "thing", "things", "item", "items", "product", "products",
    "option", "options", "max", "maximum", "min", "minimum", "total",
    "prix", "tarif", "devis", "commande", "chose", "choses", "article",
    "articles", "produit", "produits",
    # standalone trigger verbs/words that are never the product itself
    "looking", "look", "want", "wants", "wanted", "need", "needs", "needed",
    "buy", "buying", "purchase", "purchasing", "searching", "search", "find",
    "finding", "get", "getting", "ordering", "interested", "shopping",
    "shop", "have", "having", "spend", "spending", "afford", "wish",
    "hoping", "hope", "seeking", "seek", "considering", "consider",
    "cherche", "chercher", "veux", "veut", "vouloir", "besoin", "acheter",
    "achete", "achète", "commander", "trouver", "regarde", "voudrais",
    "aimerais", "souhaite", "cherchons", "achetons",
    # informal "like" constructions ("i'd like", "would like")
    "like", "liked", "likes",
})


@lru_cache(maxsize=4)
def _build_token_stopwords(config_code: str, triggers: frozenset[str]) -> frozenset[str]:
    """Single-word surface forms to drop in the fallback extractor."""
    stop: set[str] = set(_GENERIC_NON_PRODUCT)
    # single-word triggers (e.g. "want", "need", "buy", "veux", "acheter")
    for trig in triggers:
        if " " not in trig:
            stop.add(trig)
    # connectors / splitters
    stop |= _GROUP_SPLITTERS
    return frozenset(stop)


def extract_products_fallback(sentence: Span, config: LanguageConfig) -> list[dict]:
    """Token-level product extraction that does not rely on the dependency parse.

    Strategy: strip a leading filler phrase, then walk tokens, dropping
    functional tokens (triggers, currencies, numbers, stopwords, punctuation) and
    grouping the remaining contiguous content tokens into product phrases, split
    on connectors. Robust on typo-laden text where the parser degrades.

    Returns a list of ``{"name": str, "quantity": int | None}`` dicts. Price and
    currency are resolved at sentence level by the caller.
    """
    stopwords = _build_token_stopwords(config.code, config.triggers)

    groups: list[list[Token]] = []
    current: list[Token] = []
    pending_quantity: int | None = None
    group_quantities: list[int | None] = []

    def flush() -> None:
        nonlocal current, pending_quantity
        if current:
            groups.append(current)
            group_quantities.append(pending_quantity)
        current = []
        pending_quantity = None

    for token in sentence:
        text = token.text
        low = token.lower_

        if token.is_space or token.is_punct:
            # comma/semicolon split groups; other punctuation just separates.
            if low in _GROUP_SPLITTERS or text in {",", ";"}:
                flush()
            continue

        # numbers: a small integer with nothing else may be a quantity for the
        # next content token; otherwise (prices) ignored here. A resolution spec
        # like "4k"/"1080p" is kept as content (it stays with the product).
        if (token.like_num or _SHORTHAND_AMOUNT.fullmatch(low)) and not _is_resolution(low):
            if current:
                flush()
            try:
                val = float(text.replace(",", "."))
                if val.is_integer() and 0 < val < 1000:
                    pending_quantity = int(val)
            except ValueError:
                pending_quantity = None
            continue

        # connector words split product groups
        if low in _GROUP_SPLITTERS:
            flush()
            continue

        # drop currency tokens
        if is_currency_only(low):
            continue

        # drop known non-product words (triggers, "besoin", "thing", etc.)
        if low in stopwords or _is_excluded_word(token):
            # a trigger/stop word ends the current group
            if current:
                flush()
            continue
        if token.pos_ in _STOP_POS:
            continue
        # drop verbs/aux that slipped through (e.g. "ai" from "j'ai")
        if token.pos_ in ("VERB", "AUX") and not _matches_catalog(low, config):
            if current:
                flush()
            continue

        # otherwise treat as content (product) token
        current.append(token)

    flush()

    results: list[dict] = []
    for tokens, qty in zip(groups, group_quantities, strict=False):
        # keep nouns/propn/adj-ish content; drop pure verbs unless catalog terms
        content = [
            t for t in tokens
            if (t.pos_ not in ("VERB", "AUX") or _matches_catalog(t.lower_, config))
            and not is_currency_only(t.lower_)
            and not _is_excluded_word(t)
            and not _SHORTHAND_AMOUNT.fullmatch(t.lower_)
            and t.lower_ not in _PHRASE_STOP_MODIFIERS
        ]
        if not content:
            # No usable content -> skip (avoids leaking "ai", stray verbs).
            continue
        # Drop a group that is ONLY attribute/descriptor words (no product head).
        # A token is a "head" if it is a catalog product/brand, or a content word
        # that is not a (fuzzy) attribute/descriptor. Catalog match wins over
        # attribute classification (e.g. FR "portable" is a product noun).
        has_head = any(
            _matches_catalog(t.lower_, config)
            or (
                len(t.lower_) >= 3
                and t.pos_ not in ("ADP", "DET", "PRON", "CCONJ", "SCONJ", "PART")
                and not _is_attribute_word(t.lower_, config)
            )
            for t in content
        )
        if not has_head:
            continue
        name = " ".join(t.text for t in content).strip()
        if len(name) < 3:
            continue
        results.append({"name": name, "quantity": qty})
    return results
