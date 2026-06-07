"""Tests for brand / attribute / condition detection."""

import unittest

from ector.attributes import detect_attributes, detect_brand, detect_condition


class TestBrand(unittest.TestCase):
    def test_exact(self):
        self.assertEqual(detect_brand("nike shoes"), "nike")
        self.assertEqual(detect_brand("a red iphone"), "iphone")

    def test_typo(self):
        self.assertEqual(detect_brand("adidss sneakers"), "adidas")

    def test_none(self):
        self.assertIsNone(detect_brand("plain blue shirt"))


class TestAttributes(unittest.TestCase):
    def test_colors_and_descriptors(self):
        attrs = detect_attributes("red wireless gaming mouse", "en")
        self.assertIn("red", attrs)
        self.assertIn("wireless", attrs)
        self.assertIn("gaming", attrs)

    def test_typo_color(self):
        self.assertIn("black", detect_attributes("blak laptop", "en"))

    def test_french(self):
        attrs = detect_attributes("ordinateur portable noir", "fr")
        self.assertIn("noir", attrs)

    def test_dedup(self):
        attrs = detect_attributes("red red shirt", "en")
        self.assertEqual(attrs.count("red"), 1)


class TestCondition(unittest.TestCase):
    def test_new(self):
        self.assertEqual(detect_condition("brand new laptop", "en"), "new")

    def test_used(self):
        self.assertEqual(detect_condition("a second hand bike", "en"), "used")
        self.assertEqual(detect_condition("velo d'occasion", "fr"), "used")

    def test_refurbished(self):
        self.assertEqual(detect_condition("refurbished macbook", "en"), "refurbished")
        self.assertEqual(detect_condition("iphone reconditionné", "fr"), "refurbished")

    def test_none(self):
        self.assertIsNone(detect_condition("a laptop", "en"))


if __name__ == "__main__":
    unittest.main()
