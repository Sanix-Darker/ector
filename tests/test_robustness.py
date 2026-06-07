"""Robustness: ECTOR must never raise on arbitrary input and stay deterministic."""

import random
import unittest

from ector import extract_sync


def _random_text(rng: random.Random) -> str:
    alphabets = [
        "abcdefghijklmnopqrstuvwxyz ",
        "0123456789.,$€£ ",
        "àâçéèêëîïôûùüÿñæœ-' ",
        "!?;:/\\|@#%^&*()[]{}<>~` ",
        "日本語のテキスト中文字符 ",
    ]
    n = rng.randint(0, 60)
    pool = "".join(rng.choice(alphabets) for _ in range(3))
    return "".join(rng.choice(pool) for _ in range(n))


class TestRobustness(unittest.TestCase):
    def test_never_raises_on_random_input(self):
        rng = random.Random(2024)
        for _ in range(500):
            text = _random_text(rng)
            lang = rng.choice(["en", "fr", "xx"])
            result = extract_sync(text, lang)
            self.assertIn("products", result)
            self.assertIsInstance(result["products"], list)

    def test_edge_inputs(self):
        for text in ["", " ", "\n\t", ".", "123", "$$$", "€", "a" * 5000,
                     "?!?!", "budget", "usd", "🛒🛒🛒", "I want " * 200]:
            result = extract_sync(text, "en")
            self.assertIn("products", result)

    def test_deterministic(self):
        text = "I want a wireless mouse and a keyboard, budget 150 usd"
        first = extract_sync(text, "en")
        for _ in range(5):
            self.assertEqual(extract_sync(text, "en"), first)

    def test_none_safe_lang(self):
        # Unknown language must not raise.
        result = extract_sync("I want a laptop", "zz")
        self.assertIn("products", result)


if __name__ == "__main__":
    unittest.main()
