"""Tests for the catalog data (uniqueness, normalization, coverage)."""

import unittest

from ector.dictionary.catalog import (
    ALL_CATALOG_TERMS,
    BRANDS,
    PRODUCT_NOUNS_EN,
    PRODUCT_NOUNS_FR,
    catalog_terms_for,
)


class TestCatalog(unittest.TestCase):
    def test_all_lowercase_and_stripped(self):
        for term in ALL_CATALOG_TERMS:
            self.assertEqual(term, term.strip().lower())
            self.assertTrue(term)

    def test_combined_is_unique(self):
        self.assertEqual(len(ALL_CATALOG_TERMS), len(set(ALL_CATALOG_TERMS)))

    def test_reasonable_size(self):
        # We want a genuinely large catalog.
        self.assertGreater(len(ALL_CATALOG_TERMS), 300)

    def test_lang_buckets(self):
        en = catalog_terms_for("en")
        fr = catalog_terms_for("fr")
        self.assertIn("laptop", en)
        self.assertIn("iphone", en)  # brand present in both
        self.assertIn("ordinateur", fr)
        self.assertIn("iphone", fr)

    def test_sources_nonempty(self):
        self.assertGreater(len(PRODUCT_NOUNS_EN), 100)
        self.assertGreater(len(PRODUCT_NOUNS_FR), 50)
        self.assertGreater(len(BRANDS), 50)


if __name__ == "__main__":
    unittest.main()
