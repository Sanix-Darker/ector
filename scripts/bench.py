"""Micro-benchmark for ECTOR: throughput and latency percentiles.

Usage: .venv/bin/python scripts/bench.py [--n 5000]
"""
import argparse
import statistics
import time

from ector import extract_sync

SAMPLES = [
    ("I'm looking for a wireless gaming mouse and a keyboard, budget 150 usd", "en"),
    ("i wnat an ipone and a chargr, budjet 200 euoros", "en"),
    ("I want a refurbished macbook under 1200 usd", "en"),
    ("how much is the new red nike air for size 42", "en"),
    ("je veux un velo neuf et un casque, budget 300 euros", "fr"),
    ("je cherche un ordinateur portable d'occasion moins de 600 euros", "fr"),
    ("do you have a 4k monitor between 300 and 500 eur", "en"),
    ("I need 2 phones and a tablet for 800 usd total", "en"),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=4000)
    args = ap.parse_args()

    # warm up models + caches
    for text, lang in SAMPLES:
        extract_sync(text, lang)

    latencies = []
    t0 = time.perf_counter()
    for i in range(args.n):
        text, lang = SAMPLES[i % len(SAMPLES)]
        s = time.perf_counter()
        extract_sync(text, lang)
        latencies.append((time.perf_counter() - s) * 1000.0)
    total = time.perf_counter() - t0

    latencies.sort()

    def p(q):
        return latencies[min(len(latencies) - 1, int(len(latencies) * q))]

    print(f"runs:        {args.n}")
    print(f"throughput:  {args.n / total:.0f} calls/sec")
    print(f"mean:        {statistics.mean(latencies):.3f} ms")
    print(f"p50:         {p(0.50):.3f} ms")
    print(f"p95:         {p(0.95):.3f} ms")
    print(f"p99:         {p(0.99):.3f} ms")
    print(f"max:         {latencies[-1]:.3f} ms")


if __name__ == "__main__":
    main()
