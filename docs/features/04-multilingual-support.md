# Feature 04 — Multilingual Support

## Purpose
Support multiple languages with per-language models, triggers, fillers, and
budget hints. Currently English (`en`) and French (`fr`).

## Current behavior (as found)
- `load_spacy_model(lang)`: fr → `fr_core_news_sm`, else → `en_core_web_sm`.
- `get_triggers_and_fillers(lang)`: fr → FR lists, else EN lists.
- Budget hints chosen inside `maybe_budget` by `lang` — but `lang` not passed
  (BUG-001).

## Confirmed problems
- BUG-001: language not threaded to budget detection.
- RISK-005: existential/`attr` product detection assumes English dep labels and
  lemmas (`be`, `there`); French parses differ.
- No explicit registry; adding a language means editing several `if lang == ...`
  branches.

## Target design — language registry (`languages.py`)
A single registry maps a language code to its configuration:

```python
@dataclass(frozen=True)
class LanguageConfig:
    code: str
    model_name: str
    triggers: frozenset[str]
    trigger_regex: re.Pattern      # word-boundary alternation, precompiled
    fillers: tuple[str, ...]       # sorted longest-first
    budget_hints: frozenset[str]
    # language-specific dep/lemma hints for existential detection
    copula_lemmas: frozenset[str]  # {"be"} / {"être"}
    expletives: frozenset[str]     # {"there"} / {"il"}
    price_prepositions: frozenset[str]  # {"for","at"} / {"pour","à"}
```

- `get_language(code) -> LanguageConfig`, default `en`, raise/fallback clearly on
  unknown codes.
- Adding a language = add one module under `dictionary/<code>.py` + one registry
  entry. No scattered `if` branches.

## Decisions (normative)
- D-04-1: Single registry; default `en`; unknown codes fall back to `en` with a
  logged warning (non-breaking) — or raise `ValueError`? Decision: **fall back to
  en with a DEBUG log** to preserve current lenient behavior.
- D-04-2: Per-language dep/lemma hints captured in `LanguageConfig`, removing
  hardcoded English assumptions from logic.

## Acceptance criteria
- French budget + product extraction works (existing example `user_input_fr`).
- Adding a hypothetical third language requires only data + one registry entry.
