"""Tests for the language registry."""

import unittest

from ector.languages import get_language, supported_languages


class TestLanguageRegistry(unittest.TestCase):
    def test_supported(self):
        self.assertEqual(set(supported_languages()), {"en", "fr"})

    def test_english_config(self):
        cfg = get_language("en")
        self.assertEqual(cfg.code, "en")
        self.assertEqual(cfg.model_name, "en_core_web_sm")
        self.assertIn("need", cfg.triggers)
        self.assertIn("be", cfg.copula_lemmas)
        self.assertIn("for", cfg.price_prepositions)

    def test_french_config(self):
        cfg = get_language("fr")
        self.assertEqual(cfg.model_name, "fr_core_news_sm")
        self.assertIn("être", cfg.copula_lemmas)
        self.assertIn("pour", cfg.price_prepositions)

    def test_unknown_falls_back_to_english(self):
        self.assertEqual(get_language("xx").code, "en")
        self.assertEqual(get_language(None).code, "en")

    def test_fillers_sorted_longest_first(self):
        cfg = get_language("en")
        lengths = [len(f) for f in cfg.fillers]
        self.assertEqual(lengths, sorted(lengths, reverse=True))

    def test_trigger_regex_word_boundary(self):
        cfg = get_language("en")
        # 'get' is a trigger but must not match inside 'forget'.
        self.assertIsNone(cfg.trigger_regex.search("i will forget the milk"))
        self.assertIsNotNone(cfg.trigger_regex.search("i need a phone"))


if __name__ == "__main__":
    unittest.main()
