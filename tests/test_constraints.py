"""Tests for price-constraint parsing."""

import unittest

from ector.constraints import parse_constraint


class TestConstraints(unittest.TestCase):
    def test_max_under(self):
        c = parse_constraint("a laptop under 200 usd")
        self.assertEqual(c["type"], "max")
        self.assertEqual(c["value"], 200.0)
        self.assertEqual(c["currency"], "usd")

    def test_max_trailing(self):
        c = parse_constraint("a phone, 150 eur max")
        self.assertEqual(c["type"], "max")
        self.assertEqual(c["value"], 150.0)

    def test_min(self):
        c = parse_constraint("something over 50 dollars")
        self.assertEqual(c["type"], "min")
        self.assertEqual(c["value"], 50.0)

    def test_around(self):
        c = parse_constraint("around 100 eur")
        self.assertEqual(c["type"], "around")
        self.assertEqual(c["value"], 100.0)

    def test_between(self):
        c = parse_constraint("between 100 and 200 usd")
        self.assertEqual(c["type"], "between")
        self.assertEqual(c["min"], 100.0)
        self.assertEqual(c["max"], 200.0)

    def test_between_swapped(self):
        c = parse_constraint("from 200 to 100")
        self.assertEqual((c["min"], c["max"]), (100.0, 200.0))

    def test_french_moins_de(self):
        c = parse_constraint("moins de 300 euros")
        self.assertEqual(c["type"], "max")
        self.assertEqual(c["value"], 300.0)

    def test_french_entre(self):
        c = parse_constraint("entre 100 et 200 eur")
        self.assertEqual(c["type"], "between")
        self.assertEqual((c["min"], c["max"]), (100.0, 200.0))

    def test_none(self):
        self.assertIsNone(parse_constraint("a plain laptop"))

    def test_shorthand_k(self):
        c = parse_constraint("under 2k usd")
        self.assertEqual(c["value"], 2000.0)


if __name__ == "__main__":
    unittest.main()
