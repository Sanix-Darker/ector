"""Component tests for ector.products (needs spaCy models)."""

import unittest

from ector.languages import get_language
from ector.models import get_model
from ector.products import (
    collect_product_phrase,
    detect_quantity,
    find_main_product_tokens,
    find_preposition_price,
)


class TestProducts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.en = get_language("en")
        cls.nlp_en = get_model("en_core_web_sm")

    def _sent(self, text):
        return next(self.nlp_en(text).sents)

    def test_simple_object(self):
        sent = self._sent("I want a phone.")
        tokens = find_main_product_tokens(sent, self.en)
        self.assertEqual([t.text for t in tokens], ["phone"])

    def test_conjunct_across_price_phrase(self):
        # "a keyboard for 40 usd and a monitor": monitor is conjoined to the
        # currency token in the parse but must still be recovered as a product.
        sent = self._sent("I need a keyboard for 40 usd and a monitor.")
        tokens = find_main_product_tokens(sent, self.en)
        names = [t.text.lower() for t in tokens]
        self.assertIn("keyboard", names)
        self.assertIn("monitor", names)

    def test_conjunction(self):
        sent = self._sent("I need a phone and a charger.")
        tokens = find_main_product_tokens(sent, self.en)
        self.assertEqual([t.lemma_ for t in tokens], ["phone", "charger"])

    def test_currency_token_not_product(self):
        # "USD" must not be picked up as a product token.
        sent = self._sent("I want a smartphone for 200 USD.")
        tokens = find_main_product_tokens(sent, self.en)
        self.assertEqual([t.text for t in tokens], ["smartphone"])

    def test_phrase_excludes_price_preposition(self):
        sent = self._sent("I want a smartphone for 200 USD.")
        tokens = find_main_product_tokens(sent, self.en)
        phrase = collect_product_phrase(tokens[0], tokens)
        self.assertEqual(phrase, "smartphone")

    def test_compound_phrase(self):
        sent = self._sent("I also need a gaming console.")
        tokens = find_main_product_tokens(sent, self.en)
        phrase = collect_product_phrase(tokens[0], tokens)
        self.assertEqual(phrase.lower(), "gaming console")

    def test_quantity_detected(self):
        sent = self._sent("I want 2 phones.")
        tokens = find_main_product_tokens(sent, self.en)
        self.assertEqual(detect_quantity(tokens[0]), 2)

    def test_no_quantity(self):
        sent = self._sent("I want a phone.")
        tokens = find_main_product_tokens(sent, self.en)
        self.assertIsNone(detect_quantity(tokens[0]))

    def test_preposition_price(self):
        sent = self._sent("I want a phone for 250")
        self.assertEqual(find_preposition_price(sent, self.en), 250.0)

    def test_pound_cake_is_product(self):
        # RISK-009: "pound cake" must be a product (cake), not dropped.
        sent = self._sent("I want a pound cake.")
        tokens = find_main_product_tokens(sent, self.en)
        phrase = collect_product_phrase(tokens[0], tokens)
        self.assertIn("cake", phrase.lower())

    def test_pound_cake_keeps_currency_word_as_modifier(self):
        # Context-aware _keep_modifier: "pound" is a currency word but appears
        # with no numeric in its subtree, so it must be kept as the descriptive
        # compound-noun modifier of "cake" => "Pound cake" (not "Cake").
        sent = self._sent("I want a pound cake.")
        tokens = find_main_product_tokens(sent, self.en)
        phrase = collect_product_phrase(tokens[0], tokens)
        self.assertEqual(phrase.lower(), "pound cake")

    def test_currency_word_with_numeric_still_dropped(self):
        # "pound" whose subtree carries the numeric "200" must STILL be
        # dropped from the product phrase. This is the regression guard
        # for the context-aware fix: a currency word with numeric in its
        # subtree is treated as a price fragment, not a compound modifier.
        sent = self._sent("I want a 200-pound dumbbell.")
        tokens = find_main_product_tokens(sent, self.en)
        self.assertEqual([t.text for t in tokens], ["dumbbell"])
        phrase = collect_product_phrase(tokens[0], tokens)
        self.assertNotIn("pound", phrase.lower())
        self.assertEqual(phrase.lower(), "dumbbell")

    def test_currency_word_in_compound_phrase_kept(self):
        # "pound" with NO numeric in its subtree stays as a compound
        # noun modifier of "cake" => "pound cake". Mirrors US-003 at
        # the collect_product_phrase layer. Use a transitive verb so
        # "cake" lands as the direct object (nsubj-only inputs make
        # find_main_product_tokens return []).
        sent = self._sent("She's baking a pound cake for the party.")
        tokens = find_main_product_tokens(sent, self.en)
        phrase = collect_product_phrase(tokens[0], tokens)
        self.assertEqual(phrase.lower(), "pound cake")


if __name__ == "__main__":
    unittest.main()
