#!/usr/bin/env python3
"""Build the QA-matrix markdown summary used by CI.

Reads one or two JSON summary files emitted by ``scripts/run_user_stories.py``
or ``scripts/browser_user_stories.py`` (both accept ``--summary-json``), merges
them, and prints a markdown report to stdout. The caller is expected to
redirect to a file or ``$GITHUB_STEP_SUMMARY``.

An optional ``--baseline-csv PATH`` compares the fresh run to a captured
`docs/FEATURE_MATRIX.csv`` snapshot taken before the run, surfacing regressions
(rows that flipped to ``[!]``) and newly-green rows.

Usage::

    python scripts/qa_summary.py SCRIPT_SUMMARY.json [BROWSER_SUMMARY.json] \
        [--baseline-csv BASELINE.csv] \
        [--runner "name=rc" ...]

The ``--runner`` flags document which upstream runners contributed so the
comment calls out failures from each stage independently.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _merge(summaries: list[dict]) -> dict:
    rows: list[dict] = []
    ack_ids: set[str] = set()
    unacked: set[str] = set()
    totals = {"passed": 0, "failed": 0, "acked": 0}
    for s in summaries:
        rows.extend(s.get("rows", []))
        ack_ids.update(s.get("ack_ids", []))
        unacked.update(s.get("unacked_failures", []))
        for k, v in s.get("totals", {}).items():
            totals[k] = totals.get(k, 0) + v
    tested = totals["passed"] + totals["failed"] + totals["acked"]
    return {
        "rows": rows,
        "ack_ids": sorted(ack_ids),
        "unacked_failures": sorted(unacked),
        "totals": totals,
        "tested": tested,
    }


def _load_baseline(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    if not path.exists():
        return out
    with open(path, encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            if r.get("ID"):
                out[r["ID"]] = r.get("Status", "") or ""
    return out


def _build_markdown(
    merged: dict,
    baseline: dict[str, str] | None,
    runner_results: list[tuple[str, str]],
) -> str:
    totals = merged["totals"]
    tested = merged["tested"]
    pct = (totals["passed"] / tested * 100.0) if tested else 100.0
    # Non-numeric rc strings (e.g. ``"missing"`` for an intentionally skipped
    # runner) are informational; only numeric values drive the gate emoji so
    # the overall doesn't flip to FAIL when a runner was just not scheduled.
    runner_rcs: list[int] = []
    for _, rc in runner_results:
        try:
            runner_rcs.append(int(rc))
        except (TypeError, ValueError):
            pass
    gate_failed = any(rc != 0 for rc in runner_rcs)
    overall = "❌ **FAIL**" if gate_failed or totals["failed"] else "✅ **PASS**"

    out: list[str] = []
    out.append("<!-- qa-matrix -->")
    out.append("## 📊 QA Matrix Status")
    out.append("")
    out.append(
        f"{overall} — **{totals['passed']}/{tested} pass ({pct:.1f}%)** &middot; "
        f"{totals['failed']} unacked &middot; {totals['acked']} acknowledged &middot; "
        f"{len(merged['ack_ids'])} allowlist entries"
    )
    if runner_results:
        parts = [f"`{name}` rc={rc}" for name, rc in runner_results]
        out.append("")
        out.append("Runners: " + " &middot; ".join(parts))
    out.append("")

    if merged["unacked_failures"]:
        out.append("### ❌ Failures (will block merge until allowlisted)")
        out.append("")
        for r in merged["rows"]:
            if r["status"] == "[!]" and not r["acked"]:
                note = (r.get("notes") or "") or "(no notes)"
                if len(note) > 200:
                    note = note[:197] + "..."
                out.append(f"- `{r['id']}` ({r['method']}): {note}")
        out.append("")

    if totals["acked"]:
        out.append("### ⚠️ Acknowledged failures (in `.qa-known-failures`)")
        out.append("")
        for r in merged["rows"]:
            if r["status"] == "[!]" and r["acked"]:
                out.append(f"- `{r['id']}` ({r['method']})")
        out.append("")

    out.append("### Breakdown by method")
    out.append("")
    out.append("| Method | Passed | Failed | Acked | Total |")
    out.append("| :--- | ---: | ---: | ---: | ---: |")
    by_method: dict[str, dict[str, int]] = {}
    for r in merged["rows"]:
        m = (r.get("method") or "?").strip() or "?"
        b = by_method.setdefault(m, {"passed": 0, "failed": 0, "acked": 0})
        if r["status"] == "[✓]":
            b["passed"] += 1
        elif r["status"] == "[!]":
            if r["acked"]:
                b["acked"] += 1
            else:
                b["failed"] += 1
    for m, _ in sorted(by_method.items()):
        b = by_method[m]
        total = b["passed"] + b["failed"] + b["acked"]
        out.append(f"| `{m}` | {b['passed']} | {b['failed']} | {b['acked']} | {total} |")
    out.append("")

    if baseline is not None:
        current = {r["id"]: r["status"] for r in merged["rows"]}
        regressions: list[str] = []
        newly_green: list[str] = []
        for rid, base_status in baseline.items():
            new_status = current.get(rid, "")
            base_pass = base_status in ("[✓]", "", "[~]")
            if base_pass and new_status == "[!]":
                regressions.append(rid)
            if base_status == "[!]" and new_status == "[✓]":
                newly_green.append(rid)
        if regressions:
            out.append("### ⚠️ Regressions vs baseline")
            out.append("")
            out.append("| ID | Baseline | Current |")
            out.append("| :--- | :--- | :--- |")
            for rid in regressions:
                out.append(f"| `{rid}` | {baseline.get(rid, '')!r} | `[!]` |")
            out.append("")
        if newly_green:
            out.append("### 🌱 Newly green vs baseline")
            out.append("")
            out.append("| ID | Baseline | Current |")
            out.append("| :--- | :--- | :--- |")
            for rid in newly_green:
                out.append(f"| `{rid}` | `[!]` | `[✓]` |")
            out.append("")

    out.append("")
    out.append(
        "<sub>Allowlist: append a row ID to `docs/.qa-known-failures` to ACK a "
        "known failure inline.</sub>"
    )
    return "\n".join(out)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("summaries", nargs="+",
                        help="One or more JSON summary files to merge.")
    parser.add_argument("--baseline-csv", default="",
                        help="Optional baseline CSV for status-flip detection.")
    parser.add_argument("--runner", action="append", default=[],
                        help="Optional flag ``name=rc`` (repeatable) to surface runner exit codes.")
    args = parser.parse_args()

    summaries = [_load_json(Path(p)) for p in args.summaries]
    merged = _merge(summaries)

    baseline: dict[str, str] | None = None
    if args.baseline_csv:
        baseline = _load_baseline(Path(args.baseline_csv))

    runner_results: list[tuple[str, str]] = []
    for spec in args.runner:
        if "=" in spec:
            name, _, rc = spec.partition("=")
            # Keep ``rc`` as a raw string so non-numeric values such as
            # ``"missing"`` render verbatim in the markdown instead of being
            # coerced to ``-1`` and silently flipping the gate emoji.
            runner_results.append((name.strip(), rc.strip()))

    sys.stdout.write(_build_markdown(merged, baseline, runner_results))
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
