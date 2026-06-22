#!/usr/bin/env python3
"""Run every browser-test row in docs/FEATURE_MATRIX.csv (Verify_Method=browser).

Drives headless Chromium via Playwright through ECTOR's web showcase, asserts
the expected DOM state after each action, and writes Status ([ ]|[~]|[✓]|[!])
+ Notes back to the same matrix CSV used by scripts/run_user_stories.py.

Story DSL
---------
Input    ::= <action>:<target>     | e.g. chip:Multi-product + budget
                                  | click:#theme-toggle
                                  | select_lang:fr
                                  | (empty for "navigate, then assert only")
Expected ::= <key>:<value>(|<key>:<value>)*
   Keys    textarea_contains | textarea_equals | textarea_len_min
           jrow_min | jrow_max
           theme | bg_var | clipboard | title_contains | output_contains
           continue  (literal flag — keep page state across stories)

Run:
    python scripts/browser_user_stories.py --update
"""
from __future__ import annotations

import argparse
import atexit
import csv
import json
import re
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

from playwright.sync_api import Page, sync_playwright

ROOT = Path(__file__).resolve().parent.parent
CSV_PATH = ROOT / "docs" / "FEATURE_MATRIX.csv"
# Allowlist + summary helpers live in scripts/_qa_common.py so this runner and
# ``scripts/run_user_stories.py`` stay in lockstep on schema and semantics.
PORT = 8765
BASE = f"http://127.0.0.1:{PORT}"

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _qa_common import ALLOWLIST_PATH, load_allowlist as _load_allowlist, make_summary as _write_summary  # noqa: E402

# Server process managed by this script (created lazily, killed on exit).
_server: subprocess.Popen | None = None


# ---------- server lifecycle ----------


def _port_is_free(host: str = "127.0.0.1", port: int = PORT) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind((host, port))
            return True
        except OSError:
            return False


def _wait_until_ready(deadline_sec: int = 60) -> None:
    """Poll /api/health until models_loaded==true.

    /api/examples does not depend on spaCy warmup, so it is not a sufficient
    probe on its own. The chip stories trigger /api/extract via compute(),
    and 22 of them will silently flap if models are still warming.
    """
    deadline = time.time() + deadline_sec
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(f"{BASE}/api/health", timeout=2) as r:
                body = r.read().decode("utf-8", errors="replace")
                if r.getcode() == 200:
                    data = json.loads(body)
                    if data.get("models_loaded") is True:
                        return
        except (urllib.error.URLError, ConnectionError, OSError, json.JSONDecodeError):
            pass
        time.sleep(0.5)
    raise RuntimeError(f"uvicorn on :{PORT} never reported models_loaded=true")


def _start_server() -> None:
    global _server
    if _server is not None and _server.poll() is None:
        _wait_until_ready()
        return
    if not _port_is_free():
        # External uvicorn already up — just wait until it's ready.
        _wait_until_ready()
        return
    _server = subprocess.Popen(
        [
            sys.executable, "-m", "uvicorn", "web.app:app",
            "--host", "127.0.0.1", "--port", str(PORT), "--log-level", "warning",
        ],
        cwd=str(ROOT),
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    _wait_until_ready()


def _stop_server() -> None:
    global _server
    if _server is None:
        return
    if _server.poll() is None:
        _server.terminate()
        try:
            _server.wait(timeout=5)
        except subprocess.TimeoutExpired:
            _server.kill()


atexit.register(_stop_server)


# ---------- CSV I/O (same approach as run_user_stories.py) ----------


def _load_csv():
    with open(CSV_PATH, encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        header = next(reader)
        rows = [dict(zip(header, line)) for line in reader]
    return header, rows


def _save_csv(header, rows):
    with open(CSV_PATH, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
        w.writerow(header)
        for r in rows:
            w.writerow([r.get(c, "") for c in header])


# ---------- action dispatch ----------


def _act(page: Page, action: str) -> None:
    a = action.strip()
    if not a:
        return
    if a.startswith("click:"):
        sel = a.split(":", 1)[1].strip()
        page.locator(sel).first.click(timeout=5000)
        return
    if a.startswith("chip:"):
        label = a.split(":", 1)[1].strip()
        page.locator("button.chip", has_text=label).first.click(timeout=5000)
        return
    if a.startswith("select_lang:"):
        lang = a.split(":", 1)[1].strip()
        page.locator("#lang").select_option(lang)
        return
    if a.startswith("wait:"):
        sel = a.split(":", 1)[1].strip()
        page.locator(sel).first.wait_for(state="visible", timeout=5000)
        return
    if a.startswith("sleep:"):
        page.wait_for_timeout(int(a.split(":", 1)[1]))
        return
    raise ValueError(f"unknown action: {a!r}")


# ---------- assertion DSL ----------


def _wait_for_clipboard(page: Page, want_nonempty: bool, deadline_ms: int = 2000) -> str:
    """Poll clipboard text from the Python side until the desired state is
    reached. Avoids races against the async `navigator.clipboard.writeText(
    text).then(...)` handler in app.js without needing JS-arg semantics."""
    polls = max(1, deadline_ms // 100)
    last = ""
    for _ in range(polls):
        try:
            last = page.evaluate("navigator.clipboard.readText()")
            if want_nonempty and last.strip():
                return last
            if not want_nonempty and not last.strip():
                return last
        except Exception:  # noqa: BLE001
            pass
        page.wait_for_timeout(100)
    return last


def _wait_for_jrows(page: Page, pred) -> int:
    """Wait up to ~6s for #output .jrow count to satisfy `pred(n)`; return last count."""
    last = 0
    for _ in range(40):
        try:
            last = page.locator("#output .jrow").count()
        except Exception:  # noqa: BLE001
            last = 0
        if pred(last):
            return last
        page.wait_for_timeout(150)
    return last


def _assert(page: Page, expected_raw: str) -> list[str]:
    msgs: list[str] = []
    if not expected_raw.strip():
        return msgs
    for op in [o for o in expected_raw.split("|") if o]:
        key, _, val = op.partition(":")
        key, val = key.strip(), val.strip()
        try:
            if key == "textarea_contains":
                v = page.locator("#input").input_value()
                if val not in v:
                    msgs.append(f"textarea_contains: {val!r} missing in {v[:60]!r}")
            elif key == "textarea_equals":
                v = page.locator("#input").input_value()
                if v != val:
                    msgs.append(f"textarea_equals: {v!r} != {val!r}")
            elif key == "textarea_len_min":
                v = page.locator("#input").input_value()
                if len(v) < int(val):
                    msgs.append(f"textarea_len_min: len {len(v)} < {val}")
            elif key == "jrow_min":
                rows = _wait_for_jrows(page, lambda n: n >= int(val))
                if rows < int(val):
                    msgs.append(f"jrow_min: got {rows}, expected >= {val}")
            elif key == "jrow_max":
                rows = page.locator("#output .jrow").count()
                if rows > int(val):
                    msgs.append(f"jrow_max: {rows} > {val}")
            elif key == "theme":
                actual = page.evaluate("document.documentElement.dataset.theme")
                if actual != val:
                    msgs.append(f"theme: {actual!r} != {val!r}")
            elif key == "bg_var":
                got = page.evaluate(
                    "(t)=>getComputedStyle(document.documentElement)"
                    ".getPropertyValue(t).trim()",
                    val,
                )
                if not got:
                    msgs.append(f"bg_var {val!r}: empty")
            elif key == "clipboard":
                raw = _wait_for_clipboard(page, want_nonempty=True)
                if raw.strip() != val.strip():
                    msgs.append(f"clipboard: {raw[:60]!r} != {val[:60]!r}")
            elif key == "clipboard_contains":
                raw = _wait_for_clipboard(page, want_nonempty=True)
                if val not in raw:
                    msgs.append(f"clipboard_contains: {val!r} missing in {raw[:80]!r}")
            elif key == "lang_value":
                actual = page.evaluate(
                    "() => document.getElementById('lang').value"
                )
                if actual != val:
                    msgs.append(f"lang_value: {actual!r} != {val!r}")
            elif key == "title_contains":
                t = page.title()
                if val not in t:
                    msgs.append(f"title_contains: {t!r}")
            elif key == "continue":
                pass  # flag handled by run_story
            else:
                msgs.append(f"unknown key: {op!r}")
        except Exception as e:  # noqa: BLE001
            msgs.append(f"{key}: raised {e!r}")
    return msgs


# ---------- per-row runner ----------


def run_story(page: Page, row: dict) -> tuple[str, str]:
    action = row["Input"].strip()
    expected = row["Expected"].strip()
    has_continue = re.search(r"\bcontinue\s*:", expected) is not None
    if not has_continue:
        page.goto(BASE, wait_until="domcontentloaded", timeout=15_000)
        # Ensure examples have rendered before the action runs.
        try:
            page.locator("button.chip").first.wait_for(timeout=10_000)
        except Exception:  # noqa: BLE001
            pass
    try:
        if action:
            _act(page, action)
    except Exception as e:  # noqa: BLE001
        return "[!]", f"action failed: {e!r}"
    # Wait for chip-triggered compute() to settle if a chip was clicked.
    if action.startswith("chip:"):
        try:
            page.wait_for_load_state("networkidle", timeout=10_000)
        except Exception:  # noqa: BLE001
            pass
    try:
        msgs = _assert(page, expected)
    except Exception as e:  # noqa: BLE001
        return "[!]", f"assert raised: {e!r}"
    return ("[✓]", "PASS") if not msgs else ("[!]", "; ".join(msgs))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--update", action="store_true",
                        help="Write results back to the CSV.")
    parser.add_argument("--ids", default="",
                        help="Comma-separated story IDs to run (default: all browser rows).")
    parser.add_argument("--known-failures", default=str(ALLOWLIST_PATH),
                        help="Allowlist path; rows whose ID is listed do not block the exit code.")
    parser.add_argument("--summary-json", default="",
                        help="If set, write a machine-readable summary to this path.")
    args = parser.parse_args()

    _start_server()
    header, rows = _load_csv()
    sel = set(args.ids.split(",")) if args.ids else None
    targets = [r for r in rows if r.get("Verify_Method") == "browser"
               and (not sel or r["ID"] in sel)]
    if not targets:
        print("No rows with Verify_Method=browser in CSV.")
        return 0

    allow = _load_allowlist(Path(args.known_failures))
    unacked: list[str] = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(
            permissions=["clipboard-read", "clipboard-write"],
            viewport={"width": 1280, "height": 800},
        )
        page = ctx.new_page()
        for r in targets:
            r["Status"] = "[~]"
            t0 = time.perf_counter()
            status, note = run_story(page, r)
            dt = (time.perf_counter() - t0) * 1000
            r["Status"] = status
            acked = r["ID"] in allow
            if note == "PASS":
                r["Notes"] = "PASS"
            else:
                r["Notes"] = (f"FAIL (acked): {note}" if acked else f"FAIL: {note}")
            if status == "[!]" and not acked:
                unacked.append(r["ID"])
            print(f"{r['ID']}  browser   {status} {dt:6.1f}ms  {r['Notes'][:90]}")
        ctx.close()
        browser.close()

    if args.update:
        _save_csv(header, rows)
        print(f"\nUpdated: {CSV_PATH}")
    else:
        print("\n(dry-run; pass --update to write Status/Notes back)")

    # Build the summary rows consumed by scripts/qa_summary.py. Only include
    # rows the runner actually visited (i.e. those with a final [✓]/[!]).
    summary_rows = [
        {
            "id": r["ID"],
            "method": r["Verify_Method"],
            "status": r["Status"],
            "acked": r["ID"] in allow,
            "notes": (r.get("Notes") or "")[:200],
        }
        for r in targets
        if r["Status"] in ("[✓]", "[!]")
    ]

    rc = 0
    if args.summary_json:
        rc = _write_summary(
            summary_rows,
            allow=allow,
            unacked=unacked,
            path=Path(args.summary_json),
        )
        print(f"Wrote summary: {args.summary_json}")

    counts = {"passed": 0, "failed": 0, "acked": 0}
    for row in summary_rows:
        if row["status"] == "[✓]":
            counts["passed"] += 1
        elif row["status"] == "[!]":
            if row["acked"]:
                counts["acked"] += 1
            else:
                counts["failed"] += 1
    print(
        f"\nTotal: {len(targets)}  Passed: {counts['passed']}  "
        f"Failed (unacked): {counts['failed']}  Acked: {counts['acked']}"
    )
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
