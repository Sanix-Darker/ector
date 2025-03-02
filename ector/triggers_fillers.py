import re
import subprocess
import spacy
from spacy.util import is_package

from ector.dictionary import (
    FILLER_PHRASES_EN,
    FILLER_PHRASES_FR,
    FRENCH,
    REQUEST_TRIGGERS_EN,
    REQUEST_TRIGGERS_FR,
)

PRICE_PATTERN = re.compile(r"(\d+(?:\.\d+)?)\s?([^,\s\d]+)?", re.IGNORECASE)


def ensure_model_installed(model_name):
    """Ensure that a specific spaCy model is installed."""
    if not is_package(model_name):
        subprocess.run(["python", "-m", "spacy", "download", model_name], check=True)

def load_spacy_model(lang: str) -> spacy.language.Language:
    """
    Load and return the spaCy language model based on the provided language code.
    """

    if lang == FRENCH:
        ensure_model_installed("fr_core_news_sm")
        return spacy.load("fr_core_news_sm")
    ensure_model_installed("en_core_web_sm")
    return spacy.load("en_core_web_sm")


def get_triggers_and_fillers(lang: str):
    """
    Retrieve the request triggers and filler phrases for the given language.
    """
    if lang == FRENCH:
        return (REQUEST_TRIGGERS_FR, FILLER_PHRASES_FR)

    return (REQUEST_TRIGGERS_EN, FILLER_PHRASES_EN)


def parse_money_entity(money_text: str):
    """
    Attempt to parse a price amount and currency from a MONEY entity text.
    Returns (price, currency) or (None, None) if nothing is extracted.
    """

    if not (match := PRICE_PATTERN.search(money_text)):
        return None, None

    price = match.group(1)
    currency = match.group(2).strip(".$") if match.group(2) else None
    return price, currency.lower() if currency else None
