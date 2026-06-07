"""Snapshot current extract() behavior (post-refactor).

Run: .venv/bin/python scripts/snapshot_behavior.py
"""
import asyncio
import json

from ector import extract

CASES = [
    ("", "en"),
    ("I want to buy.", "en"),
    ("I'm looking for a new laptop.", "en"),
    ("I want a smartphone for 200 USD.", "en"),
    ("My budget is 300 USD.", "en"),
    ("My budget is 300.", "en"),
    ("I only have 150 eur.", "en"),
    ("I'm looking for a big TV. I also need a gaming console. My budget is 1200 USD.", "en"),
    ("I'm looking for a camera. my budget is 500 usd.", "en"),
    ("I am looking for a phone. My budget is abc or 12x34", "en"),
    ("I want a laptop for 500 usd or 600 eur.", "en"),
    ("I want a phone for 250", "en"),
    ("I want 2 phones.", "en"),
    ("I want a pound cake.", "en"),
    ("je n'ai que 50 euros.", "fr"),
    ("je veux un iPhone noire et aussi des Jordans. mais j'ai un budget de 300 dollars.", "fr"),
]


def main():
    out = {}
    for text, lang in CASES:
        out[f"[{lang}] {text}"] = asyncio.run(extract(text, lang))
    print(json.dumps(out, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
