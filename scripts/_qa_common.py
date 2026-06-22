"""Shared invariants for the QA-matrix CI flow.

Used by:
* ``scripts/run_user_stories.py`` and ``scripts/browser_user_stories.py`` to
  read ``docs/.qa-known-failures`` and emit the JSON summary file that
  ``scripts/qa_summary.py`` consumes.
* ``scripts/qa_gate.py`` and ``scripts/qa_runner.py`` for the runner
  registry (``ROLES``) so adding a third runner (e.g. an integration-test
  runner) is a one-line change and the workflow picks it up automatically.

Keeping this module side-effect free guarantees the runners, gate, and
workflow all agree on schema, naming, and event scope.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import NamedTuple

ROOT = Path(__file__).resolve().parent.parent
ALLOWLIST_PATH = ROOT / "docs" / ".qa-known-failures"


# ---------- QA runner registry (single source of truth) ----------


class Role(NamedTuple):
    """One QA runner registered with the CI matrix.

    ``summary_stem``
        Filename stem of the JSON written by ``--summary-json``. Convention:
        ``qa-<name>-summary``. The canonical on-disk path is
        ``./<summary_stem>.json`` (see :func:`summary_path`).
    ``runner_path``
        Path (relative to repo root) to the runner script invoked by
        ``scripts/qa_runner.py``.
    ``runs_on_push``
        ``False`` to skip this runner on push events (e.g. browser stories
        that need Playwright + Chromium). Default ``True`` (run on both
        push and pull_request).
    ``mutates_csv``
        ``False`` for read-only roles that write a summary but MUST NOT
        touch ``docs/FEATURE_MATRIX.csv`` (e.g. a future diff/perf/lint
        runner). Default ``True`` — the dispatcher passes ``--update`` to
        the runner so the canonical CSV reflects the latest status.
    ``extra_args``
        Args forwarded to the runner after ``--update`` and
        ``--summary-json``. Use ``$VAR`` placeholders — they'll be expanded
        via :func:`os.path.expandvars` so the workflow can pass through
        GHA env vars (``$QA_BASE``, secret tokens, …) without further
        shell-quoting juggling.
    """

    summary_stem: str
    runner_path: str
    runs_on_push: bool = True
    mutates_csv: bool = True
    extra_args: tuple[str, ...] = ()


# Adding a third runner is a one-line change here. The workflow,
# ``qa_gate.py``, and ``qa_runner.py`` all read from this list.
ROLES: tuple[Role, ...] = (
    Role(
        summary_stem="qa-script-summary",
        runner_path="scripts/run_user_stories.py",
        extra_args=("--base", "$QA_BASE"),
    ),
    Role(
        summary_stem="qa-browser-summary",
        runner_path="scripts/browser_user_stories.py",
        runs_on_push=False,  # skip on push (no Playwright in fast path)
    ),
)


def summary_path(stem: str, *, cwd: Path | None = None) -> Path:
    """Canonical JSON path for a role's summary: ``./<stem>.json``.

    All writers (runners) and readers (qa_gate, qa_summary) MUST go
    through this helper so paths stay consistent.
    """
    return (cwd or Path(".")) / f"{stem}.json"


def role_by_stem(stem: str) -> Role | None:
    """Look up the :class:`Role` for ``stem``. Returns ``None`` if unknown."""
    for r in ROLES:
        if r.summary_stem == stem:
            return r
    return None


def roles_for_event(is_pr: bool) -> tuple[Role, ...]:
    """Yield roles scheduled to run for this event kind."""
    return tuple(r for r in ROLES if is_pr or r.runs_on_push)


def manifest_for_event(is_pr: bool) -> dict[str, bool]:
    """Build the ``--expected`` manifest ``{summary_stem: required_bool}``.

    Every role scheduled for this event is ``True``; absent keys are
    treated as required-by-default by :mod:`scripts.qa_gate` (fail-closed).
    """
    return {r.summary_stem: True for r in roles_for_event(is_pr)}


def friendly_name(stem: str) -> str:
    """Strip ``qa-`` prefix and ``-summary`` suffix to get a short surface name.

    Inverse of the :class:`Role` ``summary_stem`` naming convention::

        "qa-script-summary" → "script"
        "qa-browser-summary" → "browser"

    Used for log-friendly output and as the canonical value of the
    ``inputs.role`` ``workflow_dispatch`` argument, so the dispatch UI
    shows a stable token ("script"/"browser") independent of the
    registry's internal stem format.
    """
    if stem.startswith("qa-"):
        stem = stem[len("qa-"):]
    if stem.endswith("-summary"):
        stem = stem[: -len("-summary")]
    return stem or "?"


def role_by_friendly_name(name: str) -> Role | None:
    """Look up a :class:`Role` by its short surface name (see :func:`friendly_name`)."""
    for r in ROLES:
        if friendly_name(r.summary_stem) == name:
            return r
    return None


def resolve_active_roles(
    *,
    is_pr: bool,
    filter_role: str = "",
    is_dispatch: bool = False,
) -> tuple[Role, ...]:
    """Pick the active :class:`Role` set for this run.

    ``is_pr``
        Whether the event is a pull_request (existing push/PR filter).
    ``is_dispatch``
        ``True`` for ``workflow_dispatch`` events. When the user
        explicitly chose the default ``role=all`` (or left the field
        blank), a manual rerun should give them **every** surface —
        including browser stories that normally need a PR runner — so
        maintainers can re-run the full matrix against a chosen ref
        without faking a PR. Set ``filter_role`` to a specific surface
        to override.
    ``filter_role``
        Empty string or ``"all"`` ⇒ on a ``workflow_dispatch`` event
        run every :class:`Role` (full matrix); on push/PR events honor
        :func:`roles_for_event`. Any other value is treated as an
        explicit override (typically from the ``workflow_dispatch``
        ``role`` input) and forces exactly that role to run regardless
        of its ``runs_on_push`` setting. Unknown values raise
        :class:`SystemExit` so the compute step fails loudly.
    """
    fr = (filter_role or "").strip()
    if not fr or fr == "all":
        if is_dispatch:
            return ROLES
        return roles_for_event(is_pr)
    target = role_by_friendly_name(fr)
    if target is None:
        known = ", ".join(friendly_name(r.summary_stem) for r in ROLES)
        raise SystemExit(
            f"unknown filter role {fr!r}; known surfaces: {known} (or 'all')"
        )
    return (target,)


def load_allowlist(path: Path = ALLOWLIST_PATH) -> set[str]:
    """Return row IDs whose ``[!]`` status is acknowledged in ``path``.

    Empty file or missing path returns ``set()``. Lines beginning with ``#``
    and blank lines are ignored. Trailing whitespace-separated comments on a
    row line are stripped (``US-003   # tracked in issue 42`` -> ``{"US-003"}``).
    """
    ids: set[str] = set()
    if not path.exists():
        return ids
    for line in path.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        ids.add(s.split()[0])
    return ids


def make_summary(
    rows: list[dict],
    *,
    allow: set[str],
    unacked: list[str],
    path: Path,
) -> int:
    """Write the JSON summary consumed by ``scripts/qa_summary.py``.

    Returns ``0`` if there are no unacked failures, else ``1``. The shape is:

    .. code-block:: json

        {
          "totals":       {"passed": int, "failed": int, "acked": int},
          "ack_ids":      ["..."],
          "unacked_failures": ["..."],
          "rows":         [{"id", "method", "status", "acked", "notes"}],
          "exit_code":    0 | 1
        }

    ``rows`` and ``allow`` are expected to come from the caller (each runner
    knows its own row state); this helper exists purely so the two runners
    cannot drift on schema or on the meaning of ``exit_code``.
    """
    counts = {"passed": 0, "failed": 0, "acked": 0}
    for row in rows:
        if row["status"] == "[✓]":
            counts["passed"] += 1
        elif row["status"] == "[!]":
            if row["acked"]:
                counts["acked"] += 1
            else:
                counts["failed"] += 1
    rc = 0 if not unacked else 1
    path.write_text(
        json.dumps(
            {
                "totals": counts,
                "ack_ids": sorted(allow),
                "unacked_failures": sorted(unacked),
                "rows": rows,
                "exit_code": rc,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return rc
