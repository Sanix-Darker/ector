"""Common words that must never be auto-corrected by fuzzy normalization.

If an input token is itself a legitimate common word, we must not "correct" it
to a catalog term (e.g. "take" -> "cake"). This is a protective stop-list.
"""

from __future__ import annotations

COMMON_WORDS_EN: frozenset[str] = frozenset({
    "the", "and", "for", "you", "are", "but", "not", "all", "any", "can",
    "her", "was", "one", "our", "out", "day", "get", "has", "him", "his",
    "how", "man", "new", "now", "old", "see", "two", "way", "who", "did",
    "its", "let", "put", "say", "she", "too", "use", "that", "this", "with",
    "have", "from", "they", "know", "want", "been", "good", "much", "some",
    "time", "very", "when", "come", "here", "just", "like", "long", "make",
    "many", "more", "only", "over", "such", "take", "than", "them", "then",
    "well", "were", "what", "your", "about", "would", "there", "their",
    "which", "could", "other", "after", "first", "never", "these", "thing",
    "think", "where", "being", "every", "great", "might", "still", "those",
    "while", "right", "left", "home", "office", "will", "also", "into",
    "best", "cheap", "cheapest", "really", "maybe", "please",
    "thanks", "hello", "today", "tomorrow", "online", "store", "shop",
    "around", "between", "something", "anything", "everything",
    "must", "should", "shall", "going", "gonna", "wanna", "down", "back",
    "help", "send", "keep", "feel", "seem",
    "able", "even", "ever", "less", "most", "next", "open", "real", "same",
    "sure", "true", "each", "else", "free", "full", "high", "kind",
    "last", "late", "live", "love", "made", "mean", "mind", "move",
    "name", "near", "part", "play", "read", "room", "side", "size",
    "sort", "stay", "talk", "team", "turn", "type", "view", "wait",
    "walk", "week", "word", "work", "year", "pay", "cost",
    "deal", "sale", "price", "color", "colour", "white", "black", "green",
    "blue", "red", "gray", "grey", "small", "large", "big", "fast", "slow",
    "warm", "cold", "soft", "hard", "light", "heavy",
    "sell", "sells", "selling", "sends", "tell", "tells", "dell",  # keep as-is if typed; do not let other words collapse onto brands
    "does", "done", "doing", "yes", "okay",
    # Common English words that would otherwise fuzzy-collide onto currency
    # tokens at distance 1 (via the FuzzyIndex cross-letter scan). Listing
    # them here in the protective stop-list prevents ``normalize_vocabulary``
    # from rewriting real text like ``found`` -> ``pound`` and ``quit`` ->
    # ``quid``. ``sticks`` is intentionally excluded because it is a real
    # product noun (drumsticks, chopsticks) and the typist likely means it.
    "found", "bound", "round", "sound", "mound", "wound", "hound",
    "frank", "prank", "drank", "blank", "clank",
    "books", "ducks", "rocks", "locks", "socks", "mocks",
    "quiet", "quieted", "quit", "quits",
})

COMMON_WORDS_FR: frozenset[str] = frozenset({
    "le", "la", "les", "un", "une", "des", "de", "du", "et", "ou", "mais",
    "pour", "avec", "sans", "dans", "sur", "sous", "par", "que", "qui", "quoi",
    "dont", "ceci", "cela", "ce", "cette", "ces", "mon", "ma", "mes", "ton",
    "ta", "tes", "son", "sa", "ses", "notre", "votre", "leur", "je", "tu",
    "il", "elle", "nous", "vous", "ils", "elles", "moi", "toi", "lui",
    "veux", "veut", "voudrais", "aimerais", "cherche", "besoin", "acheter",
    "avoir", "etre", "être", "faire", "aller", "venir", "voir", "savoir",
    "pouvoir", "vouloir", "devoir", "prendre", "donner", "trouver", "tres",
    "très", "plus", "moins", "bien", "mal", "aussi", "encore", "deja", "déjà",
    "avez", "avons", "ont", "est", "sont", "vendez", "vends", "vend",
    "ici", "maintenant", "aujourd", "demain", "hier", "bonjour",
    "merci", "svp", "petit", "petite", "grand", "grande", "gros", "grosse",
    "cher", "chere", "chère", "pas", "rien", "tout", "tous", "toute", "toutes",
    "blanc", "noir", "vert", "bleu", "rouge", "gris", "jaune", "rose",
    "neuf", "neuve", "occasion", "couleur", "taille", "prix", "magasin",
    "boutique", "ligne", "quelque", "quelques", "chose",
})


def is_common_word(token_lower: str, lang: str) -> bool:
    if lang == "fr":
        return token_lower in COMMON_WORDS_FR or token_lower in COMMON_WORDS_EN
    return token_lower in COMMON_WORDS_EN
