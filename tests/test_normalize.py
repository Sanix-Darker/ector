"""Tests for ector.normalize functional-vocabulary correction."""

import unittest

from ector.normalize import normalize_vocabulary


class TestNormalizeVocabulary(unittest.TestCase):
    def test_trigger_typos(self):
        self.assertEqual(
            normalize_vocabulary("I'm lookng for a labtop", "en"),
            "I'm looking for a laptop",
        )

    def test_budget_and_currency_typos(self):
        self.assertEqual(
            normalize_vocabulary("budjet of 100 dollr", "en"),
            "budget of 100 dollar",
        )

    def test_brand_typo(self):
        self.assertEqual(normalize_vocabulary("i want an ipone", "en"), "i want an iphone")

    def test_french(self):
        self.assertEqual(
            normalize_vocabulary("je veux un ordinateu", "fr"),
            "je veux un ordinateur",
        )

    def test_preserves_case(self):
        out = normalize_vocabulary("Labtop", "en")
        self.assertEqual(out, "Laptop")
        out2 = normalize_vocabulary("LABTOP", "en")
        self.assertEqual(out2, "LAPTOP")

    def test_preserves_digits_and_punct(self):
        out = normalize_vocabulary("I need a laptp, 2 of them!", "en")
        self.assertIn("laptop", out)
        self.assertIn("2", out)
        self.assertIn(",", out)
        self.assertIn("!", out)

    def test_unknown_words_unchanged(self):
        # A made-up product not in catalog must remain as typed.
        out = normalize_vocabulary("I want a zxqwophone", "en")
        self.assertIn("zxqwophone", out)

    def test_does_not_mangle_common_words(self):
        # Short/common words should not be aggressively rewritten.
        text = "I will take the one on the left for my home office"
        out = normalize_vocabulary(text, "en")
        # core words preserved
        for w in ["will", "take", "the", "one", "left", "home", "office"]:
            self.assertIn(w, out.lower().split())

    def test_idempotent_on_clean_text(self):
        clean = "I am looking for a laptop and a mouse"
        self.assertEqual(normalize_vocabulary(clean, "en"), clean)


if __name__ == "__main__":
    unittest.main()
