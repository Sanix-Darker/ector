#!/usr/bin/env python3
"""Dispatch one QA role's runner (single point of truth via ROLES).

The YML matrix runner step calls this with a ``summary_stem``. We look up
the matching ``Role`` in ``scripts/_qa_common.ROLES`` and exec the runner
with ``--update --summary-json <canonical path>`` plus ``role.extra_args``
(env-expanded via :func:`os.path.expandvars`).

Why a dispatcher instead of inline YML? Three reasons:

1. ``role.extra_args`` can contain ``$ENV_VAR`` placeholders (e.g.
   ``"--base", "$QA_BASE"``). ``os.path.expandvars`` substitutes them
   without requiring bash-level quoting gymnastics (``shlex.quote`` would
   *prevent* the env-var substitution by single-quoting the placeholder).
2. ``subprocess.call([...], shell=False)`` correctly splits on whitespace
   even when args contain spaces (e.g. ``--base http://host:8765``) or
   shell metacharacters.
3. Adding a new runner is a one-line change in ``_qa_common.ROLES``; the
   workflow does not need any updates here.

Usage::

    python scripts/qa_runner.py <summary_stem> [--summary-dir .]
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_REPO = _HERE.parent
sys.path.insert(0, str(_HERE))

from _qa_common import ROLES, role_by_stem, summary_path  # noqa: E402


def _build_cmd(stem: str, summary_dir: Path) -> list[str] | None:
    """Resolve the runner command line for ``stem``. Returns ``None`` on error."""
    role = role_by_stem(stem)
    if role is None:
        sys.stderr.write(
            f"FAIL: {stem!r} is not registered in scripts/_qa_common.ROLES. "
            f"Known stems: {[r.summary_stem for r in ROLES]}\n"
        )
        return None
    runner_abs = (_REPO / role.runner_path).resolve()
    cmd: list[str] = [sys.executable, str(runner_abs)]
    if role.mutates_csv:
        cmd.append("--update")
    cmd.extend(["--summary-json", str(summary_path(role.summary_stem, cwd=summary_dir))])
    for a in role.extra_args:
        cmd.append(os.path.expandvars(a))
    return cmd


def main() -> int:
    if len(sys.argv) < 2:
        sys.stderr.write("usage: qa_runner.py <summary_stem> [--summary-dir .]\n")
        return 2
    stem = sys.argv[1]
    summary_dir = Path(".")
    args = sys.argv[2:]
    if "--summary-dir" in args:
        i = args.index("--summary-dir")
        if i + 1 >= len(args):
            sys.stderr.write("qa_runner.py: --summary-dir requires a value\n")
            return 2
        summary_dir = Path(args[i + 1])
    cmd = _build_cmd(stem, summary_dir)
    if cmd is None:
        return 2
    # Echo the command for CI logs (single-quoted so $VAR shows expanded).
    print(f"+ {' '.join(repr(c) if any(ch.isspace() for ch in c) else c for c in cmd)}",
          file=sys.stderr)
    return subprocess.call(cmd)


if __name__ == "__main__":
    raise SystemExit(main())
