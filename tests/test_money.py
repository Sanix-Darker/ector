"""Unit tests for ector.money (single source of truth for price parsing).

Covers docs/testing/02-test-matrix.md - Unit - money.
"""

import unittest

from ector.money import is_currency_only, normalize_currency, parse_price


class TestParsePrice(unittest.TestCase):
    def test_symbol_suffix(self):
        self.assertEqual(parse_price("It's 25$"), (25.0, "usd"))

    def test_symbol_prefix(self):
        self.assertEqual(parse_price("$25"), (25.0, "usd"))

    def test_euro_symbol_decimal(self):
        self.assertEqual(parse_price("€9.99"), (9.99, "eur"))

    def test_code_eur(self):
        self.assertEqual(parse_price("25 eur"), (25.0, "eur"))

    def test_word_rupees(self):
        self.assertEqual(parse_price("500 Rupees"), (500.0, "inr"))

    def test_word_yen(self):
        self.assertEqual(parse_price("300 yen"), (300.0, "jpy"))

    def test_dirham_to_aed(self):
        self.assertEqual(parse_price("100 dirham"), (100.0, "aed"))

    def test_no_price(self):
        self.assertEqual(parse_price("no price here"), (None, None))

    def test_bare_number_not_price_by_default(self):
        # BUG-010: quantity-like bare numbers are not prices unless allowed.
        self.assertEqual(parse_price("2 phones"), (None, None))

    def test_bare_number_allowed_for_budget(self):
        self.assertEqual(parse_price("my budget is 300", allow_bare=True), (300.0, None))

    def test_first_currency_amount_wins(self):
        # RISK-003: first currency-qualified amount per text.
        self.assertEqual(parse_price("500 usd or 600 eur"), (500.0, "usd"))

    def test_thousands_separator_comma(self):
        self.assertEqual(parse_price("$1,000"), (1000.0, "usd"))

    def test_thousands_separator_space(self):
        self.assertEqual(parse_price("1 000 eur"), (1000.0, "eur"))

    def test_decimal_comma(self):
        self.assertEqual(parse_price("9,99 eur"), (9.99, "eur"))

    def test_mixed_separators(self):
        self.assertEqual(parse_price("1,234.56 usd"), (1234.56, "usd"))

    def test_glued_code(self):
        self.assertEqual(parse_price("25usd"), (25.0, "usd"))

    def test_shorthand_k(self):
        self.assertEqual(parse_price("2.5k usd"), (2500.0, "usd"))
        self.assertEqual(parse_price("1k eur"), (1000.0, "eur"))

    def test_misspelled_currency_word(self):
        self.assertEqual(parse_price("25 dollr"), (25.0, "usd"))
        self.assertEqual(parse_price("9 euoros"), (9.0, "eur"))

    def test_spelled_out_en(self):
        self.assertEqual(parse_price("twenty dollars"), (20.0, "usd"))
        self.assertEqual(parse_price("two hundred euros"), (200.0, "eur"))

    def test_spelled_out_fr(self):
        self.assertEqual(parse_price("deux cents euros", lang="fr"), (200.0, "eur"))

    def test_slang_currency(self):
        self.assertEqual(parse_price("50 bucks"), (50.0, "usd"))
        self.assertEqual(parse_price("20 quid"), (20.0, "gbp"))


class TestNormalizeCurrency(unittest.TestCase):
    def test_known(self):
        self.assertEqual(normalize_currency("dollars"), "usd")
        self.assertEqual(normalize_currency("€"), "eur")
        self.assertEqual(normalize_currency("YEN"), "jpy")

    def test_empty_and_none(self):
        self.assertIsNone(normalize_currency(""))
        self.assertIsNone(normalize_currency(None))


class TestIsCurrencyOnly(unittest.TestCase):
    def test_full_match_true(self):
        self.assertTrue(is_currency_only("usd"))
        self.assertTrue(is_currency_only("  € "))
        self.assertTrue(is_currency_only("Dollars"))

    def test_substring_false(self):
        # RISK-009: "pound cake" must survive.
        self.assertFalse(is_currency_only("pound cake"))
        self.assertFalse(is_currency_only("korean won doll"))

    def test_empty_false(self):
        self.assertFalse(is_currency_only(""))


if __name__ == "__main__":
    unittest.main()
