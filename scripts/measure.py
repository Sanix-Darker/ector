"""Measure ECTOR quality + throughput on the committed fixture dataset.

Usage:
    .venv/bin/python scripts/measure.py [path] [--failures N] [--category cat]
"""
import argparse
import time

from tests.fixtures.harness import evaluate, load_dataset


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path", nargs="?", default="tests/fixtures/dataset.jsonl")
    ap.add_argument("--failures", type=int, default=0)
    ap.add_argument("--kind", choices=["product", "price", "currency", "budget"], default=None)
    args = ap.parse_args()

    cases = load_dataset(args.path)
    t0 = time.perf_counter()
    m = evaluate(cases, collect_failures=max(args.failures, 0))
    dt = time.perf_counter() - t0
    print(m.summary())
    print(f"--- {len(cases)} cases in {dt:.1f}s = {len(cases)/dt:.0f} cases/sec ---")

    if args.failures:
        import json
        shown = 0
        for f in m.failures:
            c = f["case"]
            if args.kind == "budget" and c.get("expected_budget") is None:
                continue
            if args.kind == "product" and not c.get("expected_products"):
                continue
            print(repr(c["text"]), "| prof", c.get("profile"), "| lang", c.get("lang"))
            print("   expect prod={} price={} cur={} budget={}".format(
                c.get("expected_products"), c.get("expected_price"),
                c.get("expected_currency"), c.get("expected_budget")))
            print("   GOT:", json.dumps(f["got"], ensure_ascii=False))
            shown += 1
            if shown >= args.failures:
                break


if __name__ == "__main__":
    main()
