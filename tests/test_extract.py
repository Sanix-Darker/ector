import unittest
import asyncio
from ector import extract


def run_async(coro):
    """Helper to run async code in unittest."""
    return asyncio.run(coro)


class TestExtractProductRequests(unittest.TestCase):
    def test_empty_input(self):
        """Test handling of an empty string."""
        result = run_async(extract(""))
        self.assertIn("products", result)
        self.assertEqual(len(result["products"]), 0)
        self.assertNotIn("budget", result)

    def test_only_triggers_no_product_or_price(self):
        """
        Input has a trigger but no product tokens and no price mention.
        E.g. "I want to buy" but not specifying an item or cost.
        """
        user_input = "I want to buy."
        result = run_async(extract(user_input))
        self.assertIn("products", result)
        self.assertEqual(len(result["products"]), 0)

    def test_single_product_no_price(self):
        """Basic request with a product name but no price or budget."""
        user_input = "I'm looking for a new laptop."
        result = run_async(extract(user_input))
        self.assertIn("products", result)
        self.assertEqual(len(result["products"]), 1)
        self.assertEqual(result["products"][0]["product"], "New laptop")
        self.assertNotIn("price", result["products"][0])
        self.assertNotIn("currency", result["products"][0])

    def test_single_product_and_price_no_budget_keyword(self):
        """A user wants a product and mentions a price but doesn't say 'budget'."""
        user_input = "I want a smartphone for 200 USD."
        result = run_async(extract(user_input))
        self.assertIn("products", result)
        print(result)
        self.assertEqual(len(result["products"]), 1)
        product_data = result["products"][0]
        self.assertIn("Smartphone", product_data["product"])
        self.assertEqual(product_data["price"], 200.0)
        self.assertEqual(product_data["currency"], "usd")
        self.assertNotIn("budget", result)

    def test_explicit_budget_only_no_triggers(self):
        """User states only a budget with no triggers or product tokens."""
        user_input = "My budget is 300 USD."
        result = run_async(extract(user_input))
        self.assertIn("products", result)
        self.assertEqual(len(result["products"]), 0)
        self.assertIn("budget", result)
        self.assertEqual(result["budget"]["price"], 300.0)
        self.assertEqual(result["budget"]["currency"], "usd")

    def test_budget_heuristic_phrase(self):
        """
        Check detection of a budget from a phrase like 'I only have 150 eur'.
        Should not produce a product entry, only budget info.
        """
        user_input = "I only have 150 eur."
        result = run_async(extract(user_input))
        self.assertIn("products", result)
        self.assertEqual(len(result["products"]), 0)
        self.assertIn("budget", result)
        self.assertEqual(result["budget"]["price"], 150.0)
        self.assertEqual(result["budget"]["currency"], "eur")

    def test_multiple_products_and_budget(self):
        """
        Multiple product requests plus a budget line at the end.
        e.g., typical scenario:
          1) "I'm looking for a big TV."
          2) "I also need a gaming console"
          3) "My budget is 1200 USD."
        """
        user_input = (
            "I'm looking for a big TV. I also need a gaming console. "
            "My budget is 1200 USD."
        )
        result = run_async(extract(user_input))
        self.assertIn("products", result)
        self.assertEqual(len(result["products"]), 2)
        self.assertEqual(result["products"][0]["product"], "Big TV")
        self.assertNotIn("price", result["products"][0])
        self.assertEqual(result["products"][1]["product"], "Gaming console")
        self.assertNotIn("price", result["products"][1])
        self.assertIn("budget", result)
        self.assertEqual(result["budget"]["price"], 1200.0)
        self.assertEqual(result["budget"]["currency"], "usd")

    def test_trigger_and_budget_same_sentence(self):
        """
        If the user says something like:
        'I'm looking for a camera, my budget is 500 usd.'
        The method should treat it as a product request for 'camera' plus
        a budget of 500 USD.
        """
        user_input = "I'm looking for a camera. my budget is 500 usd."
        result = run_async(extract(user_input))
        self.assertIn("products", result)
        self.assertEqual(len(result["products"]), 1)
        self.assertEqual(result["products"][0]["product"], "Camera")
        self.assertNotIn("price", result["products"][0])
        self.assertIn("budget", result)
        self.assertEqual(result["budget"]["price"], 500.0)
        self.assertEqual(result["budget"]["currency"], "usd")

    def test_incorrect_money_pattern(self):
        """
        If the text includes something like 'abc' or '12x34' which doesn't match
        valid currency patterns, ensure no price/currency is extracted.
        """
        user_input = "I am looking for a phone. My budget is abc or 12x34"
        result = run_async(extract(user_input))
        self.assertIn("products", result)
        self.assertEqual(len(result["products"]), 1)
        self.assertEqual(result["products"][0]["product"], "Phone")
        self.assertNotIn("budget", result)

    def test_multiple_prices_in_one_sentence(self):
        """
        If a single sentence mentions multiple prices, e.g. 'I want a laptop for 500 usd or 600 eur'.
        By default we just pick the first match or you'd handle advanced logic.
        """
        user_input = "I want a laptop for 500 usd or 600 eur."
        result = run_async(extract(user_input))
        self.assertIn("products", result)
        self.assertEqual(len(result["products"]), 1)
        product_data = result["products"][0]
        # Expect the first match from the regex
        self.assertEqual(product_data["price"], 500.0)
        self.assertEqual(product_data["currency"], "usd")
        self.assertNotIn("budget", result)

    def test_product_with_partial_currency(self):
        """
        If the user says: 'I want a phone for 250' (no currency).
        Ensure it picks up the numeric price but currency remains None.
        """
        user_input = "I want a phone for 250"
        result = run_async(extract(user_input))
        self.assertIn("products", result)
        self.assertEqual(len(result["products"]), 1)
        product_data = result["products"][0]
        self.assertEqual(product_data["product"], "Phone")
        self.assertEqual(product_data["price"], 250.0)
        self.assertNotIn("currency", product_data)
        self.assertNotIn("budget", result)


if __name__ == "__main__":
    unittest.main()
