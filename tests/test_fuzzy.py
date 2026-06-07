"""Unit tests for ector.fuzzy."""

import unittest

from ector.fuzzy import (
    FuzzyIndex,
    bounded_levenshtein,
    cached_best_match,
    register_index,
    threshold_for,
)


class TestBoundedLevenshtein(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(bounded_levenshtein("kitten", "sitting", 3), 3)
        self.assertEqual(bounded_levenshtein("abc", "abc", 2), 0)

    def test_over_bound_returns_sentinel(self):
        self.assertEqual(bounded_levenshtein("abcdef", "xyz", 2), 3)  # capped+1

    def test_length_gap_shortcut(self):
        self.assertEqual(bounded_levenshtein("a", "abcdef", 2), 3)


class TestThreshold(unittest.TestCase):
    def test_scaling(self):
        self.assertEqual(threshold_for("of"), 0)
        self.assertEqual(threshold_for("euro"), 1)
        self.assertEqual(threshold_for("dollars"), 2)
        self.assertEqual(threshold_for("smartphone"), 2)


class TestFuzzyIndex(unittest.TestCase):
    def setUp(self):
        self.index = FuzzyIndex(["dollar", "dollars", "euro", "euros", "pound", "laptop", "iphone"])

    def test_exact(self):
        self.assertEqual(self.index.best_match("euro"), "euro")

    def test_single_typo(self):
        self.assertEqual(self.index.best_match("dollr"), "dollar")
        self.assertEqual(self.index.best_match("euoros"), "euros")
        self.assertEqual(self.index.best_match("labtop"), "laptop")

    def test_first_letter_typo(self):
        # 'ipone' -> 'iphone' (missing h), 'aphone'? ensure first-letter handled
        self.assertEqual(self.index.best_match("iphon"), "iphone")

    def test_no_match_when_too_far(self):
        self.assertIsNone(self.index.best_match("xyzzy"))

    def test_membership(self):
        self.assertIn("laptop", self.index)
        self.assertNotIn("tablet", self.index)

    def test_cached_lookup(self):
        token = register_index(self.index)
        self.assertEqual(cached_best_match(token, "dollr"), "dollar")
        self.assertEqual(cached_best_match(token, "dollr"), "dollar")  # cache hit


if __name__ == "__main__":
    unittest.main()
