"""Unit tests for ector.triggers (word-boundary trigger detection, BUG-009)."""

import unittest

from ector.languages import get_language
from ector.triggers import contains_trigger


class TestContainsTrigger(unittest.TestCase):
    def setUp(self):
        self.en = get_language("en")
        self.fr = get_language("fr")

    def test_true_for_real_trigger(self):
        self.assertTrue(contains_trigger("i need a phone", self.en))
        self.assertTrue(contains_trigger("i want a laptop", self.en))
        self.assertTrue(contains_trigger("do you have any monitors", self.en))

    def test_false_get_inside_forget(self):
        self.assertFalse(contains_trigger("i will forget the milk", self.en))

    def test_false_some_inside_awesome(self):
        self.assertFalse(contains_trigger("that is awesome", self.en))

    def test_false_get_inside_budget(self):
        # 'budget' contains 'get' but must not register as a trigger.
        self.assertFalse(contains_trigger("the budget", self.en))

    def test_french_trigger(self):
        self.assertTrue(contains_trigger("je cherche un téléphone", self.fr))
        self.assertTrue(contains_trigger("je veux un iphone", self.fr))


if __name__ == "__main__":
    unittest.main()
