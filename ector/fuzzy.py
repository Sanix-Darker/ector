"""Bounded fuzzy matching utilities for closed-class vocabulary correction.

Used to map a misspelled functional token (currency word, trigger verb, budget
word, known product/brand) to its canonical form. Designed for speed:

- bounded Levenshtein with early exit (``max_distance``),
- a candidate index bucketed by (first letter, length) so we only compare against
  plausible words,
- an LRU cache on the public ``best_match`` call.

See ``docs/features/08-typo-tolerance.md``.
"""

from __future__ import annotations

from collections.abc import Iterable
from functools import lru_cache


def bounded_levenshtein(a: str, b: str, max_distance: int) -> int:
    """Damerau-Levenshtein distance between ``a`` and ``b``, capped at ``max_distance``.

    Counts insertions, deletions, substitutions, and adjacent transpositions
    (e.g. "wnat" -> "want" is distance 1). Returns the true distance if it is
    ``<= max_distance``; otherwise returns ``max_distance + 1`` (sentinel). Uses a
    rolling three-row buffer with an early-exit when a whole row exceeds the bound.

    Examples:
        >>> bounded_levenshtein("kitten", "sitting", 3)
        3
        >>> bounded_levenshtein("abc", "abc", 2)
        0
        >>> bounded_levenshtein("abcdef", "xyz", 2)
        3
        >>> bounded_levenshtein("wnat", "want", 2)
        1
    """
    la, lb = len(a), len(b)
    if abs(la - lb) > max_distance:
        return max_distance + 1
    if la == 0:
        return lb if lb <= max_distance else max_distance + 1
    if lb == 0:
        return la if la <= max_distance else max_distance + 1

    # rows: two_back (i-2), previous (i-1), current (i)
    previous = list(range(lb + 1))
    two_back = [0] * (lb + 1)
    for i in range(1, la + 1):
        current = [i] + [0] * lb
        row_min = current[0]
        ai = a[i - 1]
        for j in range(1, lb + 1):
            cost = 0 if ai == b[j - 1] else 1
            val = min(
                previous[j] + 1,         # deletion
                current[j - 1] + 1,      # insertion
                previous[j - 1] + cost,  # substitution
            )
            # adjacent transposition
            if (
                i > 1
                and j > 1
                and ai == b[j - 2]
                and a[i - 2] == b[j - 1]
            ):
                val = min(val, two_back[j - 2] + 1)
            current[j] = val
            if val < row_min:
                row_min = val
        if row_min > max_distance:
            return max_distance + 1
        two_back = previous
        previous = current

    return previous[lb] if previous[lb] <= max_distance else max_distance + 1


def threshold_for(word: str) -> int:
    """Length-relative max edit distance allowed for a fuzzy match.

    Short words must match almost exactly; longer words tolerate more errors.

    Examples:
        >>> threshold_for("of")
        0
        >>> threshold_for("euro")
        1
        >>> threshold_for("dollars")
        2
        >>> threshold_for("smartphone")
        2
    """
    n = len(word)
    if n <= 3:
        return 0
    if n <= 6:
        return 1
    if n <= 11:
        return 2
    return 3


class FuzzyIndex:
    """An index of canonical terms supporting fast bounded fuzzy lookup.

    Buckets candidates by (first character, length) and probes neighbouring
    length buckets within the allowed distance. Exact matches short-circuit.
    """

    def __init__(self, terms: Iterable[str]):
        self._terms: set[str] = set()
        self._by_bucket: dict[tuple[str, int], list[str]] = {}
        for term in terms:
            self.add(term)

    def add(self, term: str) -> None:
        term = term.strip().lower()
        if not term or term in self._terms:
            return
        self._terms.add(term)
        key = (term[0], len(term))
        self._by_bucket.setdefault(key, []).append(term)

    def __contains__(self, term: str) -> bool:
        return term.strip().lower() in self._terms

    def __len__(self) -> int:
        return len(self._terms)

    def candidates(self, word: str, max_distance: int) -> list[str]:
        """Return candidate canonical terms plausibly within ``max_distance``."""
        word = word.lower()
        n = len(word)
        out: list[str] = []
        # First-letter bucket plus, for substitutions of the first letter, allow
        # a small set of alternatives is expensive; instead also scan same-length
        # buckets across all first letters when max_distance covers a first-char
        # substitution. To stay fast we restrict cross-letter scan to length-equal
        # bucket only.
        first_letters = {word[0]} if word else set()
        for fl in first_letters:
            for length in range(n - max_distance, n + max_distance + 1):
                out.extend(self._by_bucket.get((fl, length), ()))
        # Also consider same-length words with a different first letter (covers a
        # typo in the first character), bounded to keep it cheap.
        if max_distance >= 1:
            for (fl, length), words in self._by_bucket.items():
                if length == n and fl != (word[0] if word else ""):
                    out.extend(words)
        return out

    def best_match(self, word: str, max_distance: int | None = None) -> str | None:
        """Return the closest canonical term within threshold, or ``None``.

        Exact membership returns the word itself. Ties break on smallest distance
        then shortest term then lexicographic order for determinism.
        """
        if not word:
            return None
        w = word.lower()
        if w in self._terms:
            return w
        md = threshold_for(w) if max_distance is None else max_distance
        if md <= 0:
            return None

        best: str | None = None
        best_dist = md + 1
        for cand in self.candidates(w, md):
            d = bounded_levenshtein(w, cand, md)
            if d < best_dist or (
                d == best_dist
                and best is not None
                and (len(cand), cand) < (len(best), best)
            ):
                best, best_dist = cand, d
        return best if best is not None and best_dist <= md else None


@lru_cache(maxsize=4096)
def _cached_lookup(index_id: int, word: str, max_distance: int | None) -> str | None:
    index = _REGISTERED_INDEXES[index_id]
    return index.best_match(word, max_distance)


_REGISTERED_INDEXES: dict[int, FuzzyIndex] = {}


def register_index(index: FuzzyIndex) -> int:
    """Register an index for cached lookups; returns its id token."""
    token = id(index)
    _REGISTERED_INDEXES[token] = index
    return token


def cached_best_match(token: int, word: str, max_distance: int | None = None) -> str | None:
    """Cached best-match lookup against a previously registered index."""
    return _cached_lookup(token, word, max_distance)
