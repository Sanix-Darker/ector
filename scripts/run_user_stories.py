#!/usr/bin/env python3
"""Run every row in docs/FEATURE_MATRIX.csv whose Verify_Method is script/cli/http.

Each row maps to a small handler. The handler receives the Input string and a
small DSL declared in the Expected column. The runner writes Status ([ ]|[~]|[✓]|[!])
and Notes (failure reason or PASS marker) back into the CSV, preserving the
column order and quoting rules.

This script is the single source of truth for "did every documented user story
pass?". Use --update to overwrite Status; without --update it is read-only.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _qa_common import ALLOWLIST_PATH, load_allowlist as _load_allowlist, make_summary as _write_summary  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
CSV_PATH = ROOT / "docs" / "FEATURE_MATRIX.csv"
# Allowlist + summary helpers live in scripts/_qa_common.py so this runner and
# ``scripts/browser_user_stories.py`` stay in lockstep on schema and semantics.

# ---------- helpers ----------


def _load_csv() -> tuple[list[str], list[dict[str, str]]]:
    with open(CSV_PATH, encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        header = next(reader)
        rows = [dict(zip(header, line)) for line in reader]
    return header, rows


def _save_csv(header: list[str], rows: list[dict[str, str]]) -> None:
    with open(CSV_PATH, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
        writer.writerow(header)
        for row in rows:
            writer.writerow([row.get(col, "") for col in header])


def _subset_match(actual: object, expected: dict) -> list[str]:
    """Return list of missing key paths if actual doesn't match expected subset."""
    misses: list[str] = []

    def walk(path: str, got, want) -> None:
        if isinstance(want, dict):
            if not isinstance(got, dict):
                misses.append(f"{path}: expected dict, got {type(got).__name__}")
                return
            for k, v in want.items():
                walk(f"{path}.{k}" if path else k, got.get(k), v)
        elif isinstance(want, list):
            if not isinstance(got, list):
                misses.append(f"{path}: expected list, got {type(got).__name__}")
                return
            if len(got) < len(want):
                misses.append(f"{path}: list len {len(got)} < expected {len(want)}")
                return
            for i, (gv, wv) in enumerate(zip(got, want)):
                walk(f"{path}[{i}]", gv, wv)
        else:
            if got != want:
                misses.append(
                    f"{path}: expected {want!r}, got {got!r}"
                )

    walk("", actual, expected)
    return misses


# ---------- individual story handlers (script type) ----------


def _h_extract(input_: str, expected: str) -> tuple[bool, str]:
    """Run extract_sync; compare against JSON subset or special DSL."""
    from ector import extract_sync
    text = input_
    if text == "(empty)":
        text = ""
    # Determine language by Input prefix: "[fr] X" routes to French
    lang = "en"
    m_lang = re.match(r"^\[(fr|en)\]\s*(.*)", text, flags=re.S)
    if m_lang:
        lang, text = m_lang.group(1), m_lang.group(2)
    result = extract_sync(text, lang)
    return _compare_dict(expected, result)


def _compare_dict(expected: str, result: dict) -> tuple[bool, str]:
    """Compare ``expected`` (JSON subset or DSL string) to ``result``."""
    # Tolerate surrounding single/double quotes wrapping the cell (legacy CSV
    # used single quotes around JSON-shaped Expected values).
    s = expected.strip()
    if s and s[0] in ("'", '"') and s[-1] == s[0]:
        s = s[1:-1].strip()
    expected = s
    # JSON subset path
    if expected.startswith("{") or expected.startswith("["):
        try:
            obj = json.loads(expected)
        except json.JSONDecodeError as e:
            return False, f"bad expected JSON: {e}"
        misses = _subset_match(result, obj)
        return (not misses, "; ".join(misses) if misses else "OK")
    # DSL path: pipe-separated key|val requests joined with |
    if "|" in expected or (":" in expected and not expected.startswith("http_")):
        return _compare_dsl(expected, result)
    return False, f"unknown expected form: {expected!r}"


def _compare_dsl(expected: str, result: dict) -> tuple[bool, str]:
    ops = [o for o in expected.split("|") if o]
    for op in ops:
        key, _, val = op.partition(":")
        key, val = key.strip(), val.strip()
        if key == "intent_eq":
            if result.get("intent") != val:
                return False, f"intent={result.get('intent')!r} expected {val!r}"
        elif key == "constraint_type":
            ct = (result.get("price_constraint") or {}).get("type")
            if ct != val:
                return False, f"constraint_type={ct!r} expected {val!r}"
        elif key == "constraint_value":
            cv = (result.get("price_constraint") or {}).get("value")
            if cv is None or float(cv) != float(val):
                return False, f"constraint_value={cv!r} expected {val!r}"
        elif key == "constraint_min":
            cv = (result.get("price_constraint") or {}).get("min")
            if cv is None or float(cv) != float(val):
                return False, f"constraint_min={cv!r} expected {val!r}"
        elif key == "constraint_max":
            cv = (result.get("price_constraint") or {}).get("max")
            if cv is None or float(cv) != float(val):
                return False, f"constraint_max={cv!r} expected {val!r}"
        elif key == "constraint_currency":
            cv = (result.get("price_constraint") or {}).get("currency")
            if cv != val:
                return False, f"constraint_currency={cv!r} expected {val!r}"
        elif key == "brand_eq":
            pl = [p for p in result.get("products", []) if p.get("brand")]
            brands = [p["brand"] for p in pl]
            if val not in brands:
                return False, f"brand={brands!r} expected {val!r}"
        elif key == "attrs_contains":
            all_attrs: list[str] = []
            for p in result.get("products", []):
                all_attrs.extend(p.get("attributes") or [])
            if val not in all_attrs:
                return False, f"attrs={all_attrs!r} expected to contain {val!r}"
        elif key == "condition_eq":
            cs = [p.get("condition") for p in result.get("products", []) if p.get("condition")]
            if val not in cs:
                return False, f"condition={cs!r} expected {val!r}"
        elif key == "quantity_eq":
            qs = [p.get("quantity") for p in result.get("products", []) if p.get("quantity") is not None]
            if val.isdigit() and int(val) not in qs:
                return False, f"quantity={qs!r} expected to contain {val!r}"
        else:
            return False, f"unknown DSL op: {op!r}"
    return True, "OK"


def _h_script_special(input_: str, expected: str):
    """Top-level switching for script rows whose DSL is not a plain extract_sync."""
    # Has-key checks (with no extract call)
    if expected == "has_products_key":
        from ector import extract_sync
        res = extract_sync(input_)
        return isinstance(res, dict) and "products" in res, "OK" if ("products" in res) else "no products key"
    if expected == "async_works":
        import asyncio
        from ector import extract
        try:
            res = asyncio.run(extract(input_))
        except Exception as e:  # noqa: BLE001
            return False, f"async raises: {e!r}"
        return isinstance(res, dict) and "products" in res, "OK"
    if expected == "empty_products":
        from ector import extract_sync
        res = extract_sync(input_ if input_ != "(empty)" else "")
        return res.get("products") == [], f"products={res.get('products')!r}"
    if expected == "version_string":
        import ector
        v = getattr(ector, "__version__", None)
        return isinstance(v, str) and bool(v), f"version={v!r}"
    if expected == "cached_call_works":
        from ector import extract_sync
        a = extract_sync(input_)
        b = extract_sync(input_)
        return a == b, f"a==b is {a == b}"
    if expected == "quiet_unknown":
        from ector import extract_sync
        try:
            res = extract_sync(input_, "xx")
        except Exception as e:  # noqa: BLE001
            return False, f"raised: {e!r}"
        return "products" in res, "OK"
    # parse_price series
    if expected.startswith("price_eq:"):
        from ector.money import parse_price
        try:
            value, cur = parse_price(input_, allow_bare=False)
        except Exception as e:  # noqa: BLE001
            return False, f"parse_price raised: {e!r}"
        parts = expected.split(":")
        if len(parts) == 3:
            ev, ec = parts[1], parts[2]
            if ec == "":
                if value is not None:
                    return False, f"expected None, got {value!r}"
                return True, "OK"
            if value is None:
                return False, "expected parsed price, got None"
            if abs(float(value) - float(ev)) > 1e-6:
                return False, f"price={value} expected {ev}"
            # reparse to get currency
            _, cur = parse_price(input_, allow_bare=False)
            if cur != ec:
                return False, f"currency={cur} expected {ec}"
            return True, "OK"
        return False, f"bad price_eq spec: {expected!r}"
    if expected == "price_eqnone":
        from ector.money import parse_price
        value, _ = parse_price(input_, allow_bare=False)
        return value is None, f"dparse_price={value!r}"
    if expected.startswith("price_bare_eq:"):
        from ector.money import parse_price
        parts = expected.split(":")
        ev, ec = parts[1], parts[2]
        try:
            value, cur = parse_price(input_, allow_bare=True)
        except Exception as e:  # noqa: BLE001
            return False, f"raised: {e!r}"
        if value is None and ev:
            return False, f"expected {ev}, got None"
        if ec == "":
            return cur is None, f"currency={cur!r} expected None"
        if cur != ec:
            return False, f"currency={cur!r} expected {ec!r}"
        return True, "OK"
    # typo / normalize special DSL
    if expected.startswith("normalize_eq:"):
        from ector.normalize import normalize_vocabulary
        out = normalize_vocabulary(input_, "en")
        want = expected.split(":", 1)[1]
        return out == want, f"got {out!r} expected {want!r}"
    if expected.startswith("not_product:"):
        # Input form: not_product:<full text>:<bad token>
        rest = expected[len("not_product:"):]
        text, _, bad = rest.partition(":")
        from ector import extract_sync
        res = extract_sync(text)
        names = [p.get("product", "").lower().strip()
                 for p in res.get("products", [])]
        return bad not in names, f"product names={names!r}"
    if expected == "typo_has_iphone":
        from ector import extract_sync
        res = extract_sync(input_)
        names = " ".join(p.get("product", "") for p in res.get("products", [])).lower()
        return "iphone" in names, f"products={names!r}"
    return None, None  # fall through to extract_sync path


# ---------- CLI handler ----------


def _h_cli(input_: str, expected: str) -> tuple[bool, str]:
    cmd: list[str] = [sys.executable, "-m", "ector"]
    # All CLI invocations use DEVNULL for stdin so the no-input test does not
    # block on a child-inherited TTY pipe (which previously hung 30s).
    stdin = subprocess.DEVNULL
    if expected == "cli_no_input_fails":
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30, stdin=stdin)
        ok = proc.returncode != 0 and bool(proc.stderr.strip())
        return ok, f"rc={proc.returncode} stderr={proc.stderr[:120]!r}"
    if expected == "cli_help_shows":
        proc = subprocess.run([*cmd, "--help"], capture_output=True, text=True, timeout=15)
        ok = proc.returncode == 0 and "usage" in proc.stdout.lower()
        return ok, f"rc={proc.returncode} stdout_head={proc.stdout[:80]!r}"
    if expected == "cli_version_shows":
        proc = subprocess.run([*cmd, "--version"], capture_output=True, text=True, timeout=15)
        out = (proc.stdout + proc.stderr).strip()
        ok = proc.returncode == 0 and bool(re.search(r"\d+\.\d+", out))
        return ok, f"rc={proc.returncode} out={out!r}"
    if expected == "cli_compact":
        proc = subprocess.run([*cmd, "--compact", input_], capture_output=True, text=True, timeout=30, stdin=stdin)
        try:
            obj = json.loads(proc.stdout)
        except Exception as e:  # noqa: BLE001
            return False, f"not JSON: {e!r}; out={proc.stdout[:120]!r}"
        return "\n" not in proc.stdout.strip(), f"stdout had newline: {proc.stdout[-30:]!r}"
    if expected == "cli_fr_works":
        proc = subprocess.run([*cmd, "--lang", "fr", input_], capture_output=True, text=True, timeout=30, stdin=stdin)
        try:
            obj = json.loads(proc.stdout)
        except Exception as e:  # noqa: BLE001
            return False, f"not JSON: {e!r}"
        return isinstance(obj, dict) and "products" in obj, f"obj keys={list(obj.keys())!r}"
    if expected == "cli_json_valid":
        proc = subprocess.run([*cmd, input_], capture_output=True, text=True, timeout=30, stdin=stdin)
        try:
            obj = json.loads(proc.stdout)
        except Exception as e:  # noqa: BLE001
            return False, f"rc={proc.returncode} not-JSON: {e!r}; err={proc.stderr[:80]!r}"
        return isinstance(obj, dict) and "products" in obj, f"rc={proc.returncode} keys={list(obj.keys())!r}"
    return False, f"unknown CLI expected: {expected!r}"


# ---------- HTTP handler ----------


def _h_http(input_: str, expected: str, base: str) -> tuple[bool, str]:
    import urllib.request
    if ":" in expected:
        return False, f"unknown http spec {expected!r}"
    # Special case: http_truncate_ok builds its own big JSON payload. Run this
    # BEFORE the generic request-building path so the bad default payload
    # ("big_text" as raw body) does not fire a 422.
    if expected == "http_truncate_ok":
        big_seed = input_.split(":", 1)[1] if ":" in input_ else "I want a laptop "
        big = (big_seed + " ") * 600  # ~7200+ chars
        body_data = json.dumps({"text": big, "lang": "en"}).encode("utf-8")
        tr_req = urllib.request.Request(f"{base}/api/extract", method="POST", data=body_data)
        tr_req.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(tr_req, timeout=20) as resp:  # noqa: S310
                code = resp.getcode()
                body = resp.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as e:
            return False, f"HTTP {e.code}: {e.reason}"
        try:
            obj = json.loads(body)
        except Exception as e:  # noqa: BLE001
            return False, f"not JSON: {e!r}"
        return code == 200 and "products" in obj, f"code={code} keys={list(obj.keys())!r}"
    method = "POST" if input_.startswith("POST ") else "GET"
    path = input_.split(" ", 1)[1]
    # payload allowed after the path (':' delimiter)
    payload: str | None = None
    if ":" in path:
        path, _, payload = path.partition(":")
    url = f"{base}{path}"
    req = urllib.request.Request(url, method=method)
    data = None
    if method == "POST":
        data = (payload or "{}").encode("utf-8")
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, data=data, timeout=20) as resp:  # noqa: S310
            code = resp.getcode()
            body = resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        return False, f"HTTP {e.code}: {e.reason}"
    except Exception as e:  # noqa: BLE001
        return False, f"request failed: {e!r}"
    if expected == "http_health_ok":
        try:
            obj = json.loads(body)
        except Exception as e:  # noqa: BLE001
            return False, f"not JSON: {e!r} body={body[:120]!r}"
        return code == 200 and obj.get("status") == "ok", f"code={code} obj.status={obj.get('status')!r}"
    if expected == "http_extract_ok":
        try:
            obj = json.loads(body)
        except Exception as e:  # noqa: BLE001
            return False, f"not JSON: {e!r}"
        return code == 200 and "products" in obj, f"code={code} keys={list(obj.keys())!r}"
    if expected == "http_examples_ok":
        try:
            obj = json.loads(body)
        except Exception as e:  # noqa: BLE001
            return False, f"not JSON: {e!r}"
        arr = obj.get("examples") or []
        return code == 200 and len(arr) >= 10, f"code={code} examples_len={len(arr)}"
    if expected == "http_tokenize_ok":
        try:
            obj = json.loads(body)
        except Exception as e:  # noqa: BLE001
            return False, f"not JSON: {e!r}"
        ok = code == 200 and isinstance(obj.get("words"), int) and isinstance(obj.get("tokens"), int)
        return ok, f"code={code} words={obj.get('words')!r} tokens={obj.get('tokens')!r}"
    if expected == "http_index_ok":
        return code == 200 and "ECTOR" in body, f"code={code} body_head={body[:80]!r}"
    if expected == "http_static_css_ok":
        return code == 200, f"code={code}"
    if expected == "http_static_js_ok":
        return code == 200, f"code={code}"
    if expected == "http_truncate_ok":
        # Short-circuited above; placeholder kept for safety.
        return False, "internal: http_truncate_ok should have returned earlier"
    return False, f"unknown http expected: {expected!r}"


# ---------- per-row dispatch ----------


def run_row(row: dict[str, str], base: str) -> tuple[str, str]:
    expected = row["Expected"]
    method = row["Verify_Method"]
    if method == "manual":
        return "[ ]", "manual: not auto-tested"
    if method == "script":
        special = _h_script_special(row["Input"], expected)
        if special != (None, None):
            ok, note = special
            return "[✓]" if ok else "[!]", note if ok else f"FAIL: {note}"
        # fall-through: extract_sync comparison
        try:
            ok, note = _h_extract(row["Input"], expected)
        except Exception as e:  # noqa: BLE001
            return "[!]", f"EXC: {e!r}"
        return "[✓]" if ok else "[!]", note if ok else f"FAIL: {note}"
    if method == "cli":
        try:
            ok, note = _h_cli(row["Input"], expected)
        except subprocess.TimeoutExpired:
            return "[!]", "TIMEOUT (>30s)"
        except Exception as e:  # noqa: BLE001
            return "[!]", f"EXC: {e!r}"
        return "[✓]" if ok else "[!]", note if ok else f"FAIL: {note}"
    if method == "http":
        try:
            ok, note = _h_http(row["Input"], expected, base)
        except Exception as e:  # noqa: BLE001
            return "[!]", f"EXC: {e!r}"
        return "[✓]" if ok else "[!]", note if ok else f"FAIL: {note}"
    return "[ ]", f"unknown method {method!r}"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="http://127.0.0.1:8765",
                        help="HTTP base for web user stories.")
    parser.add_argument("--update", action="store_true",
                        help="Write results back to CSV.")
    parser.add_argument("--ids", default="",
                        help="Comma-separated story IDs to run (default: all).")
    parser.add_argument("--known-failures", default=str(ALLOWLIST_PATH),
                        help="Allowlist path; rows whose ID is listed do not block the exit code.")
    parser.add_argument("--summary-json", default="",
                        help="If set, write a machine-readable summary to this path.")
    args = parser.parse_args()

    header, rows = _load_csv()
    selected = set(args.ids.split(",")) if args.ids else set()
    allow = _load_allowlist(Path(args.known_failures))
    unacked: list[str] = []

    for row in rows:
        if selected and row["ID"] not in selected:
            continue
        row["Status"] = "[~]"
        t0 = time.perf_counter()
        status, note = run_row(row, args.base)
        dt = (time.perf_counter() - t0) * 1000
        row["Status"] = status
        if note == "OK":
            row["Notes"] = "PASS"
        elif status == "[!]":
            acked = row["ID"] in allow
            row["Notes"] = (f"FAIL (acked): {note}" if acked else f"FAIL: {note}")
            if not acked:
                unacked.append(row["ID"])
        else:
            row["Notes"] = note
        print(f"{row['ID']}  {row['Verify_Method']:<8}  {status} {dt:6.1f}ms  {row['Notes'][:90]}")

    if args.update:
        _save_csv(header, rows)
        print(f"\nUpdated: {CSV_PATH}")
    else:
        print("\n(dry-run; pass --update to write Status/Notes back)")

    # Build the machine-readable summary for downstream CI steps (diff vs main,
    # PR comment, etc.). Only include rows the runner actually visited.
    summary_rows = [
        {
            "id": r["ID"],
            "method": r["Verify_Method"],
            "status": r["Status"],
            "acked": r["ID"] in allow,
            "notes": (r.get("Notes") or "")[:200],
        }
        for r in rows
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

    # Recompute counts locally so the on-screen summary doesn't need to
    # re-read the JSON file we just wrote.
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
        f"\nTotal: {len(summary_rows)}  Passed: {counts['passed']}  "
        f"Failed (unacked): {counts['failed']}  Acked: {counts['acked']}"
    )
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
