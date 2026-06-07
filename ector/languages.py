"""Language registry: maps a language code to its full configuration.

Replaces scattered ``if lang == FRENCH`` branches with a single registry, and
captures per-language dependency/lemma hints so the product/budget logic is no
longer hardcoded to English (RISK-005).

See ``docs/features/04-multilingual-support.md``.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from functools import cache

from ector.dictionary import (
    EN_BUDGET_HINTS,
    ENGLISH,
    FILLER_PHRASES_EN,
    FILLER_PHRASES_FR,
    FR_BUDGET_HINTS,
    FRENCH,
    REQUEST_TRIGGERS_EN,
    REQUEST_TRIGGERS_FR,
)

logger = logging.getLogger("ector.languages")


def _build_trigger_regex(triggers: list[str]) -> re.Pattern[str]:
    """Build one word-boundary alternation regex from trigger phrases.

    Word boundaries prevent substring false positives such as 'get' inside
    'forget' or 'some' inside 'awesome' (BUG-009). Longer phrases are tried
    first so multi-word triggers match before their single-word prefixes.
    """
    ordered = sorted(set(triggers), key=len, reverse=True)
    alternation = "|".join(re.escape(t) for t in ordered)
    # \b works for ASCII word chars; the (?<!\w)/(?!\w) lookarounds also guard
    # apostrophe-led French triggers like "est-ce qu'il y a".
    return re.compile(rf"(?<!\w)(?:{alternation})(?!\w)", re.IGNORECASE)


@dataclass(frozen=True)
class LanguageConfig:
    """All per-language configuration needed by the extractor."""

    code: str
    model_name: str
    triggers: frozenset[str]
    trigger_regex: re.Pattern[str]
    fillers: tuple[str, ...]  # sorted longest-first for greedy stripping
    budget_hints: frozenset[str]
    copula_lemmas: frozenset[str] = field(default_factory=frozenset)
    expletives: frozenset[str] = field(default_factory=frozenset)
    price_prepositions: frozenset[str] = field(default_factory=frozenset)


def _make_config(
    code: str,
    model_name: str,
    triggers: list[str],
    fillers: list[str],
    budget_hints: list[str],
    copula_lemmas: set[str],
    expletives: set[str],
    price_prepositions: set[str],
) -> LanguageConfig:
    return LanguageConfig(
        code=code,
        model_name=model_name,
        triggers=frozenset(triggers),
        trigger_regex=_build_trigger_regex(triggers),
        fillers=tuple(sorted(set(fillers), key=len, reverse=True)),
        budget_hints=frozenset(budget_hints),
        copula_lemmas=frozenset(copula_lemmas),
        expletives=frozenset(expletives),
        price_prepositions=frozenset(price_prepositions),
    )


@cache
def _registry() -> dict[str, LanguageConfig]:
    return {
        ENGLISH: _make_config(
            code=ENGLISH,
            model_name="en_core_web_sm",
            triggers=REQUEST_TRIGGERS_EN,
            fillers=FILLER_PHRASES_EN,
            budget_hints=EN_BUDGET_HINTS,
            copula_lemmas={"be"},
            expletives={"there"},
            price_prepositions={"for", "at"},
        ),
        FRENCH: _make_config(
            code=FRENCH,
            model_name="fr_core_news_sm",
            triggers=REQUEST_TRIGGERS_FR,
            fillers=FILLER_PHRASES_FR,
            budget_hints=FR_BUDGET_HINTS,
            copula_lemmas={"être"},
            expletives={"il"},
            price_prepositions={"pour", "à"},
        ),
    }


def get_language(code: str | None) -> LanguageConfig:
    """Return the :class:`LanguageConfig` for ``code``.

    Unknown codes fall back to English with a DEBUG log (D-04-1), preserving the
    original lenient behavior.
    """
    registry = _registry()
    if code in registry:
        return registry[code]
    logger.debug("Unknown language code %r; falling back to '%s'", code, ENGLISH)
    return registry[ENGLISH]


def supported_languages() -> tuple[str, ...]:
    """Return the tuple of supported language codes."""
    return tuple(_registry().keys())
