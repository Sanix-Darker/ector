"""Request-trigger detection.

Uses the precompiled, word-boundary-aware regex from the language config so that
short triggers like 'get'/'some'/'have' no longer match inside larger words such
as 'forget'/'awesome'/'behave' (BUG-009).

See ``docs/audit/01-bug-catalog.md`` BUG-009.
"""

from __future__ import annotations

from ector.languages import LanguageConfig


def contains_trigger(text: str, config: LanguageConfig) -> bool:
    """Return True if ``text`` contains any request trigger as a whole word/phrase.

    Examples (English config):
        - "i need a phone"      -> True  ('need')
        - "i will forget it"    -> False (not 'get' inside 'forget')
        - "that is awesome"     -> False (not 'some' inside 'awesome')
    """
    return config.trigger_regex.search(text) is not None
