"""Corpus-level robustness test: run ECTOR over the committed fixture dataset
and assert per-metric thresholds (typo tolerance, Feature 08).

The dataset is deterministic (committed at tests/fixtures/dataset.jsonl). If it
is missing, it is generated on the fly with the same seed.
"""

import os
import unittest

from tests.fixtures.generator import write_dataset
from tests.fixtures.harness import evaluate, load_dataset

_DATASET = os.path.join(os.path.dirname(__file__), "fixtures", "dataset.jsonl")

# Thresholds (percent). Set a bit below current measured values to avoid
# flakiness while still guarding against regressions.
THRESHOLDS = {
    "product_recall": 97.0,
    "product_precision": 95.0,
    "price": 96.0,
    "currency": 96.0,
    "budget": 90.0,
}


class TestFixtureCorpus(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not os.path.exists(_DATASET):
            write_dataset(12000, _DATASET, seed=1234)
        cls.cases = load_dataset(_DATASET)
        cls.m = evaluate(cls.cases)

    def test_dataset_size(self):
        self.assertGreaterEqual(len(self.cases), 10000)

    def test_product_recall(self):
        rate = self.m.rate(self.m.product_items_captured, self.m.product_items_expected)
        self.assertGreaterEqual(rate, THRESHOLDS["product_recall"], self.m.summary())

    def test_product_precision(self):
        rate = self.m.rate(self.m.product_items_correct, self.m.product_items_extracted)
        self.assertGreaterEqual(rate, THRESHOLDS["product_precision"], self.m.summary())

    def test_price_accuracy(self):
        rate = self.m.rate(self.m.price_ok, self.m.price_cases)
        self.assertGreaterEqual(rate, THRESHOLDS["price"], self.m.summary())

    def test_currency_accuracy(self):
        rate = self.m.rate(self.m.currency_ok, self.m.currency_cases)
        self.assertGreaterEqual(rate, THRESHOLDS["currency"], self.m.summary())

    def test_budget_accuracy(self):
        rate = self.m.rate(self.m.budget_ok, self.m.budget_cases)
        self.assertGreaterEqual(rate, THRESHOLDS["budget"], self.m.summary())


if __name__ == "__main__":
    unittest.main()
