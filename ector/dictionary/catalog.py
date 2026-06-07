"""Giga e-commerce catalog: product nouns, brands, and category terms.

Used for two purposes:
1. Fuzzy normalization of misspelled *known* products/brands to canonical form
   (so "ipone" -> "iphone", "labtop" -> "laptop") before/within extraction.
2. Seeding the fixture generator with realistic product names.

This is intentionally large and curated for English + French commerce vocabulary.
All terms are lowercase canonical forms. Open-vocabulary products not present
here are still extracted by the parser/fallback; this catalog only *helps* known
items survive typos.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Generic product nouns (English). Single-word head nouns shoppers use.
# ---------------------------------------------------------------------------
PRODUCT_NOUNS_EN: list[str] = [
    # electronics
    "laptop", "notebook", "computer", "desktop", "monitor", "screen", "keyboard",
    "mouse", "trackpad", "webcam", "microphone", "headphones", "headset",
    "earbuds", "earphones", "speaker", "soundbar", "amplifier", "turntable",
    "phone", "smartphone", "tablet", "phablet", "smartwatch", "watch", "charger",
    "powerbank", "battery", "cable", "adapter", "dongle", "router", "modem",
    "printer", "scanner", "projector", "television", "tv", "console", "controller",
    "joystick", "gamepad", "drone", "camera", "camcorder", "lens", "tripod",
    "gimbal", "flashdrive", "harddrive", "ssd", "memory", "ram", "processor",
    "cpu", "gpu", "motherboard", "graphicscard", "fan", "cooler", "case",
    # home & kitchen
    "fridge", "refrigerator", "freezer", "oven", "microwave", "stove", "cooktop",
    "dishwasher", "blender", "mixer", "toaster", "kettle", "coffeemaker",
    "grinder", "juicer", "fryer", "airfryer", "pot", "pan", "skillet", "knife",
    "cutlery", "plate", "bowl", "mug", "cup", "glass", "bottle", "thermos",
    "vacuum", "broom", "mop", "iron", "heater", "humidifier", "purifier",
    "lamp", "bulb", "chandelier", "mattress", "pillow", "blanket", "duvet",
    "sheet", "towel", "curtain", "rug", "carpet", "sofa", "couch", "chair",
    "armchair", "stool", "table", "desk", "shelf", "bookshelf", "wardrobe",
    "cabinet", "dresser", "bed", "crib", "mirror", "clock",
    # fashion & apparel
    "shirt", "tshirt", "blouse", "sweater", "hoodie", "jacket", "coat", "blazer",
    "vest", "cardigan", "jeans", "trousers", "pants", "shorts", "skirt", "dress",
    "gown", "suit", "tie", "scarf", "gloves", "hat", "cap", "beanie", "socks",
    "underwear", "belt", "shoes", "sneakers", "boots", "sandals", "heels",
    "loafers", "slippers", "bag", "backpack", "handbag", "purse", "wallet",
    "suitcase", "luggage", "sunglasses", "glasses", "ring", "necklace",
    "bracelet", "earrings", "pendant", "brooch", "umbrella",
    # beauty & health
    "perfume", "cologne", "lotion", "cream", "serum", "moisturizer", "cleanser",
    "shampoo", "conditioner", "soap", "toothbrush", "toothpaste", "razor",
    "trimmer", "hairdryer", "straightener", "lipstick", "mascara", "foundation",
    "concealer", "sunscreen", "vitamins", "supplement", "protein", "thermometer",
    # food & grocery
    "coffee", "tea", "juice", "water", "soda", "wine", "beer", "chocolate",
    "candy", "cookies", "biscuits", "cereal", "rice", "pasta", "flour", "sugar",
    "honey", "oil", "vinegar", "sauce", "spices", "snacks", "chips", "nuts",
    "apple", "apples", "banana", "bananas", "orange", "oranges", "milk", "cheese",
    "yogurt", "bread", "butter", "eggs", "cake",
    # sports & outdoors
    "bicycle", "bike", "scooter", "skateboard", "treadmill", "dumbbell",
    "kettlebell", "barbell", "yogamat", "tent", "sleepingbag", "backpack",
    "ball", "football", "basketball", "racket", "racquet", "golf", "helmet",
    "kayak", "paddle", "fishingrod", "binoculars",
    # baby & kids
    "stroller", "carseat", "diapers", "bottle", "pacifier", "toy", "doll",
    "blocks", "puzzle", "bicycle",
    # office & stationery
    "pen", "pencil", "marker", "notebook", "binder", "stapler", "calculator",
    "whiteboard", "envelope", "folder", "tape",
    # automotive & tools
    "tire", "tyre", "battery", "drill", "hammer", "screwdriver", "wrench",
    "saw", "sander", "toolbox", "ladder", "flashlight", "generator",
]

# ---------------------------------------------------------------------------
# Generic product nouns (French).
# ---------------------------------------------------------------------------
PRODUCT_NOUNS_FR: list[str] = [
    "ordinateur", "portable", "ecran", "écran", "clavier", "souris", "casque",
    "ecouteurs", "écouteurs", "enceinte", "telephone", "téléphone", "smartphone",
    "tablette", "montre", "chargeur", "batterie", "cable", "câble", "imprimante",
    "televiseur", "téléviseur", "console", "manette", "appareil", "camera",
    "caméra", "objectif", "trepied", "trépied", "clavier", "frigo",
    "refrigerateur", "réfrigérateur", "congelateur", "four", "micro-ondes",
    "lave-vaisselle", "mixeur", "grille-pain", "bouilloire", "cafetiere",
    "cafetière", "aspirateur", "fer", "lampe", "ampoule", "matelas", "oreiller",
    "couverture", "drap", "serviette", "rideau", "tapis", "canape", "canapé",
    "chaise", "fauteuil", "table", "bureau", "etagere", "étagère", "armoire",
    "lit", "miroir", "chemise", "tshirt", "pull", "veste", "manteau", "jean",
    "pantalon", "short", "jupe", "robe", "costume", "cravate", "echarpe",
    "écharpe", "gants", "chapeau", "casquette", "chaussettes", "ceinture",
    "chaussures", "baskets", "bottes", "sandales", "sac", "sacados",
    "portefeuille", "valise", "lunettes", "bague", "collier", "bracelet",
    "parapluie", "parfum", "creme", "crème", "shampooing", "savon", "rasoir",
    "cafe", "café", "the", "thé", "jus", "eau", "vin", "biere", "bière",
    "chocolat", "bonbons", "gateau", "gâteau", "riz", "pates", "pâtes",
    "velo", "vélo", "trottinette", "ballon", "tente", "stylo", "crayon",
    "calculatrice", "perceuse", "marteau", "tournevis", "pneu", "lampe-torche",
]

# ---------------------------------------------------------------------------
# Brands (case-insensitive canonical lowercase).
# ---------------------------------------------------------------------------
BRANDS: list[str] = [
    # tech
    "apple", "iphone", "ipad", "ipod", "macbook", "imac", "airpods", "samsung",
    "galaxy", "google", "pixel", "huawei", "xiaomi", "oneplus", "oppo", "vivo",
    "nokia", "motorola", "sony", "playstation", "ps5", "ps4", "xbox", "nintendo",
    "switch", "microsoft", "surface", "dell", "hp", "lenovo", "asus", "acer",
    "msi", "razer", "logitech", "corsair", "intel", "amd", "nvidia", "geforce",
    "lg", "panasonic", "philips", "bose", "jbl", "sennheiser", "beats", "anker",
    "gopro", "canon", "nikon", "fujifilm", "kodak", "garmin", "fitbit", "kindle",
    "amazon", "echo", "alexa", "roku", "tcl", "hisense", "vizio",
    # fashion / sport
    "nike", "adidas", "puma", "reebok", "newbalance", "asics", "converse",
    "vans", "jordan", "jordans", "underarmour", "fila", "lacoste", "levis",
    "zara", "uniqlo", "gucci", "prada", "versace", "balenciaga", "rolex",
    "casio", "fossil", "timberland", "northface", "patagonia", "columbia",
    # home / appliances / auto
    "dyson", "ikea", "kitchenaid", "nespresso", "delonghi", "bosch", "siemens",
    "whirlpool", "tefal", "tesla", "toyota", "honda", "ford", "bmw", "audi",
    "michelin", "dewalt", "makita", "blackdecker",
]

# Combined canonical catalog (deduped lowercase).
ALL_CATALOG_TERMS: list[str] = sorted(
    {t.lower() for t in (PRODUCT_NOUNS_EN + PRODUCT_NOUNS_FR + BRANDS)}
)


def catalog_terms_for(lang: str) -> list[str]:
    """Catalog terms relevant for a language (brands are language-agnostic)."""
    if lang == "fr":
        return sorted({t.lower() for t in (PRODUCT_NOUNS_FR + BRANDS)})
    return sorted({t.lower() for t in (PRODUCT_NOUNS_EN + BRANDS)})
