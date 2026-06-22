#!/usr/bin/env python3
"""Aggregate runner exit codes from the QA-matrix summary JSON files.

This is the final gate step in ``.github/workflows/qa.yml`` and replaces an
inline heredoc that tripped YAML escaping. Each positional argument (or, by
default, every stem registered in ``scripts/_qa_common.ROLES``) is the path
to a summary written by ``--summary-json``. A ``--expected`` manifest (a JSON
object mapping ``summary_stem -> bool``) tells the gate which runners were
scheduled to run, with the following semantics:

* **Stem explicitly listed as ``true``**: ``--summary-json`` must exist with
  ``exit_code == 0`` (or the fail-closed behaviour applies — missing/empty/
  unparseable file -> FAIL).
* **Stem explicitly listed as ``false``**: skip regardless of file state.
* **Stem absent from the manifest (the fail-open default)**: treated as
  not-required, with a per-stem ``WARN`` so the contributor immediately
  sees the stale/declared-out-of-band situation. The gate still passes;
  the staleness is loud.

Why fail-open by default: a contributor renaming a runner file in
``scripts/_qa_common.ROLES`` is the easiest way the manifest becomes stale.
With a fail-closed default, the contributor sees only ``MISSING_RC=1`` and
must puzzle out whether the problem is the runner script, the manifest, the
ROLES entry, or downstream. With fail-open + WARN, they see the WARN
naming the undeclared stem and know which manifest to refresh.

Usage::

    # Auto-discover every ROLES summary path in --summary-dir:
    python scripts/qa_gate.py --expected /tmp/qa-expected.json

    # Or pass exactly the paths you care about (useful for local debugging):
    python scripts/qa_gate.py --expected /tmp/qa-expected.json \\
        ./qa-script-summary.json ./qa-browser-summary.json

The manifest schema::

    {"<summary stem>": <bool>, ...}

E.g. for a push workflow that should only run the script+cli+http stories::

    {"qa-script-summary": true, "qa-browser-summary": false}
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Ensure ``_qa_common`` imports cleanly whether invoked as a script or via
# ``python -m scripts.qa_gate``.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _qa_common import ROLES, friendly_name, role_by_stem, summary_path  # noqa: E402

MISSING_RC = 1  # any missing/empty/unreadable summary is a gate failure


def _load_exit_code(path: Path) -> tuple[int, list[str], str]:
    """Return ``(rc, unacked_failures, error_msg_if_any)`` for a summary file.

    Missing, empty, unreadable, or unparseable paths bubble up ``MISSING_RC``
    so the gate fails closed. Callers decide whether to ignore that via the
    ``--expected`` manifest.
    """
    if not path.exists():
        return MISSING_RC, [], f"missing summary file: {path}"
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as e:
        return MISSING_RC, [], f"cannot read {path}: {e}"
    if not raw.strip():
        return MISSING_RC, [], f"empty summary file: {path}"
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        return MISSING_RC, [], f"{path} is not valid JSON: {e}"
    try:
        rc = int(data.get("exit_code", 0) or 0)
    except (TypeError, ValueError):
        rc = MISSING_RC
    return rc, list(data.get("unacked_failures", [])), ""


def _load_expected(path: str) -> dict[str, bool]:
    """Read the manifest. Returns ``{}`` if path is empty or unparseable."""
    if not path:
        return {}
    try:
        raw = Path(path).read_text(encoding="utf-8")
    except OSError as e:
        print(f"WARN: cannot read --expected manifest {path}: {e}", file=sys.stderr)
        return {}
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"WARN: --expected manifest {path} is not valid JSON: {e}", file=sys.stderr)
        return {}
    if not isinstance(data, dict):
        print(f"WARN: --expected manifest {path} is not a JSON object; ignoring", file=sys.stderr)
        return {}
    return {str(k): bool(v) for k, v in data.items()}


def _resolve_summaries(args: argparse.Namespace) -> list[Path]:
    """Pick a list of summary paths to gate over.

    If the caller passed any positional paths, use them verbatim (useful
    for local debugging). Otherwise auto-derive every registered role's
    canonical ``./<summary_stem>.json`` in ``--summary-dir``.
    """
    if args.summaries:
        return [Path(p) for p in args.summaries]
    summary_dir = Path(args.summary_dir)
    return [summary_path(r.summary_stem, cwd=summary_dir) for r in ROLES]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--expected", required=True,
                        help="Path to a JSON mapping ``stem -> required (bool)``. "
                             "Stems explicitly mapped to ``true`` are enforced "
                             "fail-closed (a missing/empty/unparseable summary "
                             "is a gate failure). Stems explicitly mapped to "
                             "``false`` are skipped without checking. Stems "
                             "absent from the manifest default to NOT required "
                             "(fail-open) and produce a per-stem WARN so a "
                             "stale manifest is loud-visible after a rename.")
    parser.add_argument("--summary-dir", default=".",
                        help="Directory holding role summary files (default repo root). "
                             "Used to auto-derive paths when no positional args are given.")
    parser.add_argument("summaries", nargs="*",
                        help="Optional explicit summary paths; default: all ROLES stems "
                             "in --summary-dir.")
    args = parser.parse_args()

    expected = _load_expected(args.expected)
    paths = _resolve_summaries(args)
    overall_rc = 0
    seen_unknown = False
    for p in paths:
        stem = p.stem
        if role_by_stem(stem) is None and not seen_unknown:
            print(
                f"WARN: {stem!r} is not registered in scripts/_qa_common.ROLES; "
                f"known stems: {[r.summary_stem for r in ROLES]}",
                file=sys.stderr,
            )
            seen_unknown = True
        # Fail-OPEN default for undeclared stems: a contributor renaming a
        # runner file in scripts/_qa_common.ROLES shouldn't gate-block on a
        # stale manifest. The WARN below makes the staleness loud so the
        # contributor knows where to refresh the manifest. Explicit
        # true/false entries in --expected still enforce as before.
        if stem not in expected:
            print(
                f"WARN: stem {stem!r} is not declared in --expected manifest; "
                f"treating as not-required. Add the stem explicitly to enforce.",
                file=sys.stderr,
            )
            is_required = False
        else:
            is_required = expected[stem]
        rc, unacked, err = _load_exit_code(p)
        name = friendly_name(stem)
        # Fail-OPEN semantic must hold for BOTH the missing-file AND the
        # exit-code!=0 outcomes of an undeclared stem. The previous
        # two-branch structure guarded the missing-file path but still
        # burnt ``rc`` to ``overall_rc`` regardless of ``is_required``,
        # which meant a renamed-and-stale-manifest contributor with a
        # genuine runner failure would still gate. Collapsing the
        # branches into a single 3-way switch fixes that asymmetry.
        problem: str | bool = False
        if err:
            problem = err
        elif rc != 0:
            problem = f"unacked failures: {unacked}"
        if not problem:
            print(f"PASS: {name} clean", file=sys.stderr)
        elif is_required:
            print(f"FAIL: {name} {problem} (required)", file=sys.stderr)
            # ``problem`` truthy implies ``rc >= 1``: ``err`` was set
            # (``_load_exit_code`` returns ``MISSING_RC`` for any error)
            # or ``rc != 0`` directly. ``MISSING_RC`` fallback is
            # therefore unreachable here.
            overall_rc |= rc
        else:
            print(f"NOTE: {name} not required; skipped ({problem})", file=sys.stderr)
    if overall_rc != 0:
        print(
            f"\nGATE FAIL (rc={overall_rc}): unacked rows + missing-required "
            f"summaries above will block merge.",
            file=sys.stderr,
        )
    else:
        print(f"\nGATE PASS: every required runner is clean.", file=sys.stderr)
    return overall_rc


if __name__ == "__main__":
    raise SystemExit(main())
