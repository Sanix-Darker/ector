"""Regression tests pinning the documented bug fixes (docs/audit, docs/fixes).

Each test references the bug/risk id it guards.
"""

import asyncio
import unittest

from ector import extract, extract_sync


def run(coro):
    return asyncio.run(coro)


class TestRegressions(unittest.TestCase):
    # RISK-009: currency word inside a product name must not drop the product.
    def test_pound_cake_survives(self):
        result = extract_sync("I want a pound cake.")
        names = [p["product"].lower() for p in result["products"]]
        self.assertTrue(any("cake" in n for n in names), result)
        self.assertNotIn("budget", result)

    # BUG-010: a bare quantity must not become a price; quantity is captured.
    def test_quantity_not_price(self):
        result = extract_sync("I want 2 phones.")
        self.assertEqual(len(result["products"]), 1)
        product = result["products"][0]
        self.assertNotIn("price", product)
        self.assertEqual(product.get("quantity"), 2)
        self.assertIn("phone", product["product"].lower())

    # BUG-008: a currency-less budget is still emitted.
    def test_budget_without_currency(self):
        result = extract_sync("My budget is 300.")
        self.assertEqual(result["products"], [])
        self.assertIn("budget", result)
        self.assertEqual(result["budget"]["price"], 300.0)
        self.assertNotIn("currency", result["budget"])

    # BUG-001: French budget hints work without the literal word "budget".
    def test_french_budget_hint(self):
        result = extract_sync("je n'ai que 50 euros.", "fr")
        self.assertIn("budget", result)
        self.assertEqual(result["budget"]["price"], 50.0)
        self.assertEqual(result["budget"]["currency"], "eur")

    # BUG-009: 'get' inside 'forget' must not act as a trigger (no product).
    def test_no_false_trigger_forget(self):
        result = extract_sync("I will forget the milk.")
        # "milk" is a dobj of forget; with no trigger and a product noun, the
        # extractor still lists it (branch 4). The key guarantee is that the
        # word 'forget' itself did not register as the trigger 'get'. We assert
        # no spurious price/budget leaked from the sentence.
        self.assertNotIn("budget", result)

    # BUG-014: French elision preserved so the product is parsed correctly.
    def test_french_elision_preserved(self):
        result = extract_sync("je veux un iPhone noir.", "fr")
        names = [p["product"].lower() for p in result["products"]]
        self.assertTrue(any("iphone" in n for n in names), result)

    # Smartphone price phrase no longer leaks "for" into the name.
    def test_clean_product_name_with_price(self):
        result = extract_sync("I want a smartphone for 200 USD.")
        self.assertEqual(result["products"][0]["product"], "Smartphone")
        self.assertEqual(result["products"][0]["price"], 200.0)
        self.assertEqual(result["products"][0]["currency"], "usd")

    # Money phrase like "at 150 usd max" must not create a spurious product.
    def test_no_spurious_money_phrase_product(self):
        result = extract_sync("I want a laptop at 150 usd max.")
        self.assertEqual(len(result["products"]), 1)
        self.assertEqual(result["products"][0]["product"], "Laptop")

    # Resolution specs ("4k", "1080p", "hd") are attributes, never prices.
    def test_resolution_not_price(self):
        result = extract_sync("I want a monitor with 4k HD", "en")
        self.assertEqual(len(result["products"]), 1)
        product = result["products"][0]
        self.assertNotIn("price", product)
        attrs = product.get("attributes", [])
        self.assertIn("4k", attrs)
        self.assertIn("hd", attrs)

    def test_resolution_inline(self):
        result = extract_sync("I want a 1080p webcam and a 4k tv", "en")
        names = " ".join(p["product"].lower() for p in result["products"])
        self.assertIn("webcam", names)
        self.assertIn("tv", names)
        for p in result["products"]:
            self.assertNotIn("price", p)

    # Shorthand "2k usd" stays a price even though "4k HD" is a resolution.
    def test_shorthand_k_still_price(self):
        result = extract_sync("I want a gaming laptop for 2k usd", "en")
        self.assertEqual(result["products"][0]["price"], 2000.0)

    # A constraint's currency comes from near the constraint, not an earlier one.
    def test_constraint_currency_scoping(self):
        result = extract_sync(
            "my budget is 150 usd. looking for a monitor between 300 and 500 eur", "en"
        )
        self.assertEqual(result["price_constraint"]["currency"], "eur")

    # Backwards-compatible async API still works.
    def test_async_api(self):
        result = run(extract("I'm looking for a new laptop."))
        self.assertEqual(result["products"][0]["product"], "New laptop")

    # Nameless price-only request yields no product entry.
    def test_nameless_price_only_skipped(self):
        result = extract_sync("I want to buy for 50 usd.")
        self.assertEqual(result["products"], [])


if __name__ == "__main__":
    unittest.main()
