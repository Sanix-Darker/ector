"""Unit tests for ector.budget."""

import unittest

from ector.budget import build_budget, is_budget
from ector.languages import get_language


class TestIsBudget(unittest.TestCase):
    def setUp(self):
        self.en = get_language("en")
        self.fr = get_language("fr")

    def test_budget_word_en(self):
        self.assertTrue(is_budget("my budget is 300", self.en))

    def test_hint_en(self):
        self.assertTrue(is_budget("i only have 150 eur", self.en))

    def test_not_budget(self):
        self.assertFalse(is_budget("i want a laptop", self.en))

    def test_french_hint_without_budget_word(self):
        # BUG-001: French hints must be used.
        self.assertTrue(is_budget("je n'ai que 50 euros", self.fr))

    def test_french_budget_word(self):
        self.assertTrue(is_budget("j'ai un budget de 300 dollars", self.fr))


class TestBuildBudget(unittest.TestCase):
    def test_with_currency(self):
        self.assertEqual(build_budget(300.0, "usd"), {"price": 300.0, "currency": "usd"})

    def test_without_currency(self):
        # BUG-008: currency-less budget is still emitted.
        self.assertEqual(build_budget(300.0, None), {"price": 300.0})

    def test_zero_or_negative_is_none(self):
        self.assertIsNone(build_budget(0.0, "usd"))
        self.assertIsNone(build_budget(-5.0, "usd"))

    def test_none_price(self):
        self.assertIsNone(build_budget(None, "usd"))


if __name__ == "__main__":
    unittest.main()
