"""Measurement harness: run ECTOR over labelled fixtures and score results.

Matching rules (typo-tolerant):
- A product is "captured" if any extracted product's head word fuzzy-matches the
  expected canonical head (distance within threshold), OR the expected head is a
  substring of an extracted product (and vice-versa).
- Price matches if |extracted - expected| <= 0.01 for some product (single-price
  cases) or appears among extracted prices.
- Currency matches exactly after normalization.
- Budget matches on price (and currency when expected).

The harness returns aggregate metrics and a list of failures for inspection.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field

from ector import extract_sync
from ector.fuzzy import bounded_levenshtein, threshold_for


def _head(name: str) -> str:
    toks = name.lower().split()
    return toks[-1] if toks else name.lower()


def product_captured(expected_head: str, extracted_names: list[str]) -> bool:
    eh = expected_head.lower()
    for name in extracted_names:
        low = name.lower()
        if eh in low or low in eh:
            return True
        h = _head(name)
        md = max(1, threshold_for(eh))
        if bounded_levenshtein(eh, h, md) <= md:
            return True
        # also compare against every token of the extracted phrase
        for tok in low.split():
            if bounded_levenshtein(eh, tok, md) <= md:
                return True
    return False


@dataclass
class Metrics:
    total: int = 0
    product_cases: int = 0
    product_captured_cases: int = 0
    product_items_expected: int = 0
    product_items_captured: int = 0
    # precision: extracted products that match an expected head
    product_items_extracted: int = 0
    product_items_correct: int = 0
    price_cases: int = 0
    price_ok: int = 0
    currency_cases: int = 0
    currency_ok: int = 0
    budget_cases: int = 0
    budget_ok: int = 0
    by_profile: dict = field(default_factory=dict)
    failures: list = field(default_factory=list)
    precision_failures: list = field(default_factory=list)

    def rate(self, ok: int, total: int) -> float:
        return (ok / total * 100.0) if total else 100.0

    def summary(self) -> str:
        lines = [
            f"cases:              {self.total}",
            f"product item recall:{self.rate(self.product_items_captured, self.product_items_expected):6.2f}%"
            f"  ({self.product_items_captured}/{self.product_items_expected})",
            f"product precision:  {self.rate(self.product_items_correct, self.product_items_extracted):6.2f}%"
            f"  ({self.product_items_correct}/{self.product_items_extracted})",
            f"product case recall:{self.rate(self.product_captured_cases, self.product_cases):6.2f}%"
            f"  ({self.product_captured_cases}/{self.product_cases})",
            f"price accuracy:     {self.rate(self.price_ok, self.price_cases):6.2f}%"
            f"  ({self.price_ok}/{self.price_cases})",
            f"currency accuracy:  {self.rate(self.currency_ok, self.currency_cases):6.2f}%"
            f"  ({self.currency_ok}/{self.currency_cases})",
            f"budget accuracy:    {self.rate(self.budget_ok, self.budget_cases):6.2f}%"
            f"  ({self.budget_ok}/{self.budget_cases})",
        ]
        if self.by_profile:
            lines.append("by profile (product item recall):")
            for prof, (ok, tot) in sorted(self.by_profile.items()):
                lines.append(f"  {prof:<10} {self.rate(ok, tot):6.2f}%  ({ok}/{tot})")
        return "\n".join(lines)


def evaluate(cases: list[dict], collect_failures: int = 50) -> Metrics:
    m = Metrics()
    for case in cases:
        m.total += 1
        result = extract_sync(case["text"], case["lang"])
        products = result.get("products", [])
        names = [p.get("product", "") for p in products]
        prices = [p.get("price") for p in products if p.get("price") is not None]
        currencies = [p.get("currency") for p in products if p.get("currency")]

        prof = case.get("profile", "?")
        prof_ok, prof_tot = m.by_profile.get(prof, (0, 0))

        # products
        expected_products = case.get("expected_products") or []
        case_all_captured = True
        for head in expected_products:
            m.product_items_expected += 1
            prof_tot += 1
            if product_captured(head, names):
                m.product_items_captured += 1
                prof_ok += 1
            else:
                case_all_captured = False
        m.by_profile[prof] = (prof_ok, prof_tot)
        if expected_products:
            m.product_cases += 1
            if case_all_captured:
                m.product_captured_cases += 1

        # precision: each extracted product should match some expected head.
        for name in names:
            m.product_items_extracted += 1
            if any(product_captured(h, [name]) for h in expected_products):
                m.product_items_correct += 1
            elif len(m.precision_failures) < collect_failures:
                m.precision_failures.append(
                    {"text": case["text"], "lang": case["lang"],
                     "expected": expected_products, "extra": name, "got": names}
                )

        # price
        if case.get("expected_price") is not None:
            m.price_cases += 1
            exp = case["expected_price"]
            budget_price = (result.get("budget") or {}).get("price")
            candidates = list(prices)
            if budget_price is not None:
                candidates.append(budget_price)
            if any(abs(p - exp) <= 0.01 for p in candidates):
                m.price_ok += 1

        # currency
        if case.get("expected_currency") is not None:
            m.currency_cases += 1
            exp = case["expected_currency"]
            budget_cur = (result.get("budget") or {}).get("currency")
            if exp in currencies or exp == budget_cur:
                m.currency_ok += 1

        # budget
        if case.get("expected_budget") is not None:
            m.budget_cases += 1
            exp = case["expected_budget"]
            got = result.get("budget")
            ok = got is not None and abs(got.get("price", -1) - exp["price"]) <= 0.01
            if ok and exp.get("currency"):
                ok = got.get("currency") == exp["currency"]
            if ok:
                m.budget_ok += 1

        # collect a few failures for debugging
        failed = (
            (expected_products and not case_all_captured)
            or (case.get("expected_price") is not None and not any(
                abs(p - case["expected_price"]) <= 0.01
                for p in prices + ([(result.get("budget") or {}).get("price")]
                                   if (result.get("budget") or {}).get("price") is not None else [])
            ))
        )
        if failed and len(m.failures) < collect_failures:
            m.failures.append({"case": case, "got": result})

    return m


def load_dataset(path: str) -> list[dict]:
    cases = []
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                cases.append(json.loads(line))
    return cases
