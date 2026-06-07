"""Attribute vocabulary: colors, sizes, conditions, materials, descriptors.

Used (a) to structure product attributes (Feature 09) and (b) to prevent bare
descriptors from being emitted as standalone products in the fallback extractor.

All canonical lowercase. English + French.
"""

from __future__ import annotations

COLORS_EN = {
    "black", "white", "red", "blue", "green", "yellow", "orange", "purple",
    "pink", "brown", "gray", "grey", "silver", "gold", "beige", "navy",
    "turquoise", "violet", "maroon", "teal",
}
COLORS_FR = {
    "noir", "noire", "blanc", "blanche", "rouge", "bleu", "bleue", "vert",
    "verte", "jaune", "orange", "violet", "violette", "rose", "marron", "gris",
    "grise", "argent", "or", "beige", "turquoise",
}

SIZES = {
    "xs", "s", "m", "l", "xl", "xxl", "xxxl", "small", "medium", "large",
    "petit", "petite", "moyen", "moyenne", "grand", "grande", "mini", "maxi",
    "compact", "slim", "oversized",
}

STORAGE_UNITS = {"gb", "tb", "mb", "go", "to", "ko"}

# Display / resolution spec terms. These are attributes (specs), never prices.
# "4k", "1080p", "8k", "hd", "uhd", "qhd", "fhd", "retina", "oled", "amoled",
# "lcd", "led", etc.
RESOLUTIONS = {
    "4k", "8k", "2k", "5k", "1080p", "720p", "1440p", "2160p",
    "hd", "uhd", "fhd", "qhd", "shd", "full-hd", "fullhd", "retina",
    "oled", "amoled", "lcd", "led", "qled", "ips", "hdr",
}

MATERIALS_EN = {
    "leather", "cotton", "wool", "silk", "plastic", "metal", "steel", "wood",
    "wooden", "glass", "ceramic", "rubber", "aluminum", "aluminium", "carbon",
    "denim", "linen", "nylon", "polyester",
}
MATERIALS_FR = {
    "cuir", "coton", "laine", "soie", "plastique", "metal", "métal", "acier",
    "bois", "verre", "ceramique", "céramique", "caoutchouc", "aluminium",
    "carbone", "lin", "nylon",
}

# Generic quality/style descriptors that are attributes, not products.
DESCRIPTORS_EN = {
    "new", "used", "cheap", "cheapest", "affordable", "premium", "luxury",
    "wireless", "wired", "portable", "smart", "fast", "slow", "waterproof",
    "rechargeable", "foldable", "lightweight", "heavy", "durable", "compact",
    "gaming", "professional", "pro", "basic", "advanced", "mini", "ergonomic",
    "vintage", "modern", "classic", "fancy", "elegant", "stylish", "high",
    "resolution", "quality", "best", "top", "good", "great",
}
DESCRIPTORS_FR = {
    "nouveau", "nouvelle", "neuf", "neuve", "occasion", "cher", "chere",
    "chère", "abordable", "premium", "luxe", "rapide", "lent", "portable",
    "intelligent", "etanche", "étanche", "rechargeable", "pliable", "leger",
    "léger", "lourd", "durable", "compact", "gaming", "professionnel", "pro",
    "basique", "avance", "avancé", "ergonomique", "vintage", "moderne",
    "classique", "elegant", "élégant", "haut", "haute", "qualite", "qualité",
    "meilleur", "meilleure", "bon", "bonne", "grand", "grande",
}

# Condition vocabulary -> canonical condition value.
CONDITION_MAP = {
    # new
    "new": "new", "brand new": "new", "brand-new": "new", "neuf": "new",
    "neuve": "new", "neufs": "new", "neuves": "new", "sealed": "new",
    # used
    "used": "used", "second hand": "used", "second-hand": "used",
    "preowned": "used", "pre-owned": "used", "occasion": "used",
    "d'occasion": "used", "seconde main": "used",
    # refurbished
    "refurbished": "refurbished", "refurb": "refurbished",
    "reconditionne": "refurbished", "reconditionné": "refurbished",
    "remis a neuf": "refurbished", "remis à neuf": "refurbished",
}


def colors(lang: str) -> set[str]:
    return COLORS_FR | COLORS_EN if lang == "fr" else COLORS_EN


def materials(lang: str) -> set[str]:
    return MATERIALS_FR | MATERIALS_EN if lang == "fr" else MATERIALS_EN


def descriptors(lang: str) -> set[str]:
    return DESCRIPTORS_FR | DESCRIPTORS_EN if lang == "fr" else DESCRIPTORS_EN


def all_attribute_words(lang: str) -> frozenset[str]:
    """Every attribute-like word for a language (colors+sizes+materials+descriptors)."""
    base: set[str] = set()
    base |= colors(lang)
    base |= SIZES
    base |= STORAGE_UNITS
    base |= RESOLUTIONS
    base |= materials(lang)
    base |= descriptors(lang)
    return frozenset(base)
