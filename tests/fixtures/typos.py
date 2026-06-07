"""Deterministic typo engine for fixture generation.

Given a random seed, produces realistic typos of a word/phrase across several
profiles. All randomness flows through a passed-in ``random.Random`` so datasets
are reproducible.
"""

from __future__ import annotations

import random

# Approximate QWERTY adjacency for keyboard-slip typos.
_QWERTY_NEIGHBORS = {
    "a": "qwsz", "b": "vghn", "c": "xdfv", "d": "serfcx", "e": "wsdr",
    "f": "drtgvc", "g": "ftyhbv", "h": "gyujnb", "i": "ujko", "j": "huikmn",
    "k": "jiolm", "l": "kop", "m": "njk", "n": "bhjm", "o": "iklp",
    "p": "ol", "q": "wa", "r": "edft", "s": "awedxz", "t": "rfgy",
    "u": "yhji", "v": "cfgb", "w": "qase", "x": "zsdc", "y": "tghu",
    "z": "asx",
}


def _delete(word: str, rng: random.Random) -> str:
    if len(word) <= 2:
        return word
    i = rng.randrange(len(word))
    return word[:i] + word[i + 1:]


def _insert(word: str, rng: random.Random) -> str:
    i = rng.randrange(len(word) + 1)
    ch = rng.choice("abcdefghijklmnopqrstuvwxyz")
    return word[:i] + ch + word[i:]


def _transpose(word: str, rng: random.Random) -> str:
    if len(word) < 2:
        return word
    i = rng.randrange(len(word) - 1)
    return word[:i] + word[i + 1] + word[i] + word[i + 2:]


def _substitute(word: str, rng: random.Random) -> str:
    if not word:
        return word
    i = rng.randrange(len(word))
    ch = rng.choice("abcdefghijklmnopqrstuvwxyz")
    return word[:i] + ch + word[i + 1:]


def _keyboard_slip(word: str, rng: random.Random) -> str:
    if not word:
        return word
    i = rng.randrange(len(word))
    c = word[i].lower()
    neighbors = _QWERTY_NEIGHBORS.get(c)
    if not neighbors:
        return word
    repl = rng.choice(neighbors)
    return word[:i] + repl + word[i + 1:]


def _double(word: str, rng: random.Random) -> str:
    if not word:
        return word
    i = rng.randrange(len(word))
    return word[:i] + word[i] + word[i:]


_EDITS = [_delete, _insert, _transpose, _substitute, _keyboard_slip, _double]


def typo_word(word: str, rng: random.Random, edits: int = 1) -> str:
    """Apply ``edits`` random single-character edits to ``word``."""
    if len(word) < 4:
        return word  # too short to typo safely
    out = word
    for _ in range(edits):
        edit = rng.choice(_EDITS)
        candidate = edit(out, rng)
        if candidate:
            out = candidate
    return out


def maybe_typo_phrase(phrase: str, rng: random.Random, profile: str) -> str:
    """Apply a typo profile to a (possibly multi-word) phrase.

    Profiles:
      - "clean": unchanged.
      - "single": one edit on one word.
      - "multi": one edit on up to two words.
      - "keyboard": keyboard-slip on one word.
      - "transpose": transposition on one word.
      - "case": random casing.
      - "spacing": collapse/extra spaces.
    """
    words = phrase.split()
    if not words:
        return phrase

    if profile == "clean":
        return phrase
    if profile == "case":
        return " ".join(
            w.upper() if rng.random() < 0.3 else (w.capitalize() if rng.random() < 0.3 else w.lower())
            for w in words
        )
    if profile == "spacing":
        sep = rng.choice(["  ", " ", "\t "])
        return sep.join(words)
    if profile == "keyboard":
        i = rng.randrange(len(words))
        words[i] = _keyboard_slip(words[i], rng) if len(words[i]) >= 4 else words[i]
        return " ".join(words)
    if profile == "transpose":
        i = rng.randrange(len(words))
        words[i] = _transpose(words[i], rng) if len(words[i]) >= 4 else words[i]
        return " ".join(words)
    if profile == "multi":
        idxs = list(range(len(words)))
        rng.shuffle(idxs)
        for i in idxs[: min(2, len(words))]:
            if len(words[i]) >= 4:
                words[i] = typo_word(words[i], rng, edits=1)
        return " ".join(words)
    # default "single"
    long_idxs = [i for i, w in enumerate(words) if len(w) >= 4]
    if long_idxs:
        i = rng.choice(long_idxs)
        words[i] = typo_word(words[i], rng, edits=1)
    return " ".join(words)
