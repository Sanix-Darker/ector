"""Unit tests for ector.text_utils."""

import unittest

from ector.text_utils import clean_phrase, normalize_text


class TestNormalizeText(unittest.TestCase):
    def test_preserves_apostrophe(self):
        # BUG-014: apostrophes must survive (English contraction).
        self.assertIn("I'm", normalize_text("Hi, I'm here"))

    def test_preserves_french_elision(self):
        # BUG-014: "j'ai" must not become "j.ai".
        self.assertEqual(normalize_text("j'ai un budget"), "j'ai un budget")

    def test_preserves_decimal(self):
        self.assertEqual(normalize_text("9.99"), "9.99")

    def test_preserves_hyphen(self):
        self.assertEqual(normalize_text("est-ce"), "est-ce")

    def test_comma_becomes_period(self):
        self.assertEqual(normalize_text("a, b"), "a. b")

    def test_semicolon_becomes_period(self):
        self.assertEqual(normalize_text("a phone; a charger"), "a phone. a charger")


class TestCleanPhrase(unittest.TestCase):
    def test_strip_filler_and_article(self):
        self.assertEqual(
            clean_phrase("i need a big red apple", ["i need a", "i need"]),
            "Big red apple",
        )

    def test_longest_filler_first(self):
        # Ensures deterministic longest-match (BUG-012).
        self.assertEqual(
            clean_phrase("i want a laptop", ["i want", "i want a"]),
            "Laptop",
        )

    def test_article_only(self):
        self.assertEqual(clean_phrase("the laptop", []), "Laptop")

    def test_trim_whitespace(self):
        self.assertEqual(clean_phrase("  a phone ", []), "Phone")

    def test_empty(self):
        self.assertEqual(clean_phrase("", []), "")


if __name__ == "__main__":
    unittest.main()
