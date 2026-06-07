"""Smoke tests for the FastAPI showcase (no network; uses TestClient).

Skipped automatically if FastAPI is not installed (it lives in the optional
``web`` extra).
"""

import unittest

try:
    from fastapi.testclient import TestClient

    from web.app import app

    _HAVE_WEB = True
except Exception:  # pragma: no cover - exercised only when extra missing
    _HAVE_WEB = False


@unittest.skipUnless(_HAVE_WEB, "web extra (fastapi) not installed")
class TestWebApp(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_health(self):
        r = self.client.get("/api/health")
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertEqual(body["status"], "ok")
        self.assertIn("en", body["languages"])
        self.assertIn("github.com", body["repo"])
        self.assertGreater(body["max_chars"], 0)

    def test_examples(self):
        r = self.client.get("/api/examples")
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.json()["examples"])

    def test_extract_en(self):
        r = self.client.post(
            "/api/extract",
            json={"text": "I want a wireless mouse for 25 usd", "lang": "en"},
        )
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertTrue(data["products"])
        self.assertEqual(data["products"][0]["price"], 25.0)
        self.assertEqual(data["intent"], "buy")

    def test_extract_fr_budget(self):
        r = self.client.post(
            "/api/extract",
            json={"text": "je veux un velo, budget 300 euros", "lang": "fr"},
        )
        data = r.json()
        self.assertIn("budget", data)
        self.assertEqual(data["budget"]["price"], 300.0)

    def test_tokenize_counts(self):
        r = self.client.post(
            "/api/tokenize",
            json={"text": "I want a wireless mouse, budget 150 usd", "lang": "en"},
        )
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertEqual(data["words"], 8)
        self.assertGreaterEqual(data["tokens"], 9)  # comma is its own token
        self.assertEqual(data["chars"], len("I want a wireless mouse, budget 150 usd"))

    def test_tokenize_empty(self):
        r = self.client.post("/api/tokenize", json={"text": "", "lang": "en"})
        self.assertEqual(r.json(), {"words": 0, "tokens": 0, "chars": 0})

    def test_tokenize_unknown_lang_falls_back(self):
        r = self.client.post("/api/tokenize", json={"text": "je veux un velo", "lang": "zz"})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["words"], 4)

    def test_index_served(self):
        r = self.client.get("/")
        self.assertEqual(r.status_code, 200)
        self.assertIn("ECTOR", r.text)

    def test_unknown_lang_falls_back(self):
        r = self.client.post("/api/extract", json={"text": "a laptop", "lang": "xx"})
        self.assertEqual(r.status_code, 200)


if __name__ == "__main__":
    unittest.main()
