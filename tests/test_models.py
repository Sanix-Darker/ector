"""Tests for ector.models caching and download policy."""

import unittest
from unittest import mock

import ector.models as models


class TestModelCaching(unittest.TestCase):
    def setUp(self):
        models.clear_model_cache()

    def tearDown(self):
        models.clear_model_cache()

    def test_model_loaded_once_and_cached(self):
        # BUG-005: spacy.load must run only once per model name.
        sentinel = object()
        with mock.patch("ector.models.is_package", return_value=True), mock.patch(
            "ector.models.spacy.load", return_value=sentinel
        ) as load:
            first = models.get_model("en_core_web_sm")
            second = models.get_model("en_core_web_sm")
        self.assertIs(first, sentinel)
        self.assertIs(second, sentinel)
        self.assertEqual(load.call_count, 1)

    def test_missing_model_raises_actionable_error(self):
        # BUG-006: no implicit download by default; helpful message.
        with mock.patch("ector.models.is_package", return_value=False), mock.patch.dict(
            "os.environ", {}, clear=False
        ):
            import os

            os.environ.pop(models.AUTO_DOWNLOAD_ENV, None)
            with self.assertRaises(OSError) as ctx:
                models.get_model("nonexistent_model_xyz")
        self.assertIn("not installed", str(ctx.exception))

    def test_auto_download_uses_current_interpreter(self):
        with mock.patch("ector.models.is_package", return_value=False), mock.patch(
            "ector.models.spacy.load", return_value=object()
        ), mock.patch("ector.models.subprocess.run") as run, mock.patch.dict(
            "os.environ", {models.AUTO_DOWNLOAD_ENV: "1"}
        ):
            models.get_model("some_model")
        run.assert_called_once()
        args = run.call_args[0][0]
        import sys

        self.assertEqual(args[0], sys.executable)
        self.assertIn("download", args)


if __name__ == "__main__":
    unittest.main()
