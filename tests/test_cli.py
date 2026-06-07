"""Tests for the ECTOR CLI."""

import io
import json
import unittest
from contextlib import redirect_stdout
from unittest import mock

from ector.cli import main


class TestCli(unittest.TestCase):
    def _run(self, argv):
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = main(argv)
        return code, buf.getvalue()

    def test_positional_text_en(self):
        code, out = self._run(["I want a laptop for 150 usd"])
        self.assertEqual(code, 0)
        data = json.loads(out)
        self.assertTrue(data["products"])
        self.assertEqual(data["products"][0]["price"], 150.0)

    def test_lang_fr(self):
        code, out = self._run(["--lang", "fr", "je veux un iPhone."])
        self.assertEqual(code, 0)
        data = json.loads(out)
        names = [p["product"].lower() for p in data["products"]]
        self.assertTrue(any("iphone" in n for n in names))

    def test_compact_output(self):
        code, out = self._run(["--compact", "I need a phone."])
        self.assertEqual(code, 0)
        self.assertNotIn("\n  ", out)  # no pretty indentation
        json.loads(out)  # still valid JSON

    def test_no_input_errors(self):
        # No arg, no file, and a tty stdin -> argparse error -> SystemExit(2).
        with mock.patch("sys.stdin") as stdin:
            stdin.isatty.return_value = True
            with self.assertRaises(SystemExit):
                main([])


if __name__ == "__main__":
    unittest.main()
