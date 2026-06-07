"""Tests for intent classification."""

import unittest

from ector.intent import classify_intent


class TestIntent(unittest.TestCase):
    def test_price_check(self):
        self.assertEqual(classify_intent("how much is the iphone", True), "price_check")
        self.assertEqual(classify_intent("quel est le prix du velo", True), "price_check")

    def test_availability(self):
        self.assertEqual(classify_intent("do you have a laptop in stock", True), "availability")

    def test_compare(self):
        self.assertEqual(classify_intent("compare the iphone and the pixel", True), "compare")

    def test_buy(self):
        self.assertEqual(classify_intent("i want to buy a laptop", True), "buy")
        self.assertEqual(classify_intent("je veux un velo", True), "buy")

    def test_browse_when_no_products(self):
        self.assertEqual(classify_intent("just looking thanks", False), "browse")

    def test_buy_default_with_products(self):
        self.assertEqual(classify_intent("a red shirt", True), "buy")


if __name__ == "__main__":
    unittest.main()
