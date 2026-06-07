"""Command-line interface for ECTOR.

Usage examples::

    ector "I want a laptop for 150 usd"
    ector --lang fr "je veux un iPhone, budget 300 dollars"
    ector --file input.txt
    echo "I need a phone" | ector

See ``docs/features/07-cli.md``.
"""

from __future__ import annotations

import argparse
import json
import sys

from ector import __version__
from ector.api import extract_sync
from ector.languages import supported_languages


def _read_input(args: argparse.Namespace) -> str:
    """Resolve the input text: explicit arg > --file > STDIN (D-07-2)."""
    if args.text:
        return args.text
    if args.file:
        with open(args.file, encoding="utf-8") as handle:
            return handle.read()
    if not sys.stdin.isatty():
        return sys.stdin.read()
    return ""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ector",
        description="Extract eCommerce products and a budget from free text.",
    )
    parser.add_argument("text", nargs="?", help="Input text. If omitted, reads --file or STDIN.")
    parser.add_argument(
        "--lang",
        default="en",
        choices=supported_languages(),
        help="Language of the input (default: en).",
    )
    parser.add_argument("--file", help="Read input text from a file path.")
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--pretty",
        dest="pretty",
        action="store_true",
        default=True,
        help="Pretty-print JSON (default).",
    )
    group.add_argument(
        "--compact",
        dest="pretty",
        action="store_false",
        help="Emit compact single-line JSON.",
    )
    parser.add_argument("--version", action="version", version=f"ector {__version__}")
    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI entry point. Returns a process exit code."""
    parser = build_parser()
    args = parser.parse_args(argv)

    text = _read_input(args)
    if not text.strip():
        parser.error("no input provided (pass text, --file, or pipe via STDIN)")

    try:
        result = extract_sync(text, args.lang)
    except OSError as exc:  # missing model, etc.
        print(str(exc), file=sys.stderr)
        return 2

    indent = 2 if args.pretty else None
    separators = None if args.pretty else (",", ":")
    print(json.dumps(result, indent=indent, separators=separators, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
