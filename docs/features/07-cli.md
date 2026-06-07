# Feature 07 — Command-Line Interface (NEW / MISSING)

## Purpose
Let users run ECTOR from the shell without writing Python.

## Status
Missing today. This is an additive enhancement.

## Target design (`cli.py`, entry point `ector`)
```
ector "I want a laptop for 150 usd, budget 200 eur" --lang en
ector --lang fr --file input.txt
echo "je veux un iPhone, budget 300 dollars" | ector --lang fr
```

### Behavior
- Accept text as a positional argument, `--file PATH`, or STDIN.
- `--lang {en,fr}` (default `en`).
- `--pretty` (default) / `--compact` JSON output.
- Exit code 0 on success; non-zero with a clear message on bad input/missing
  model.

### Implementation notes
- Use `argparse` (stdlib; no new dependency).
- Print `json.dumps(result, ensure_ascii=False, indent=2)`.
- Register console script in `pyproject.toml`:
  ```toml
  [project.scripts]
  ector = "ector.cli:main"
  ```
- Also support `python -m ector` via `ector/__main__.py`.

## Decisions (normative)
- D-07-1: stdlib `argparse`, no extra dependency.
- D-07-2: STDIN / argument / `--file` input precedence: explicit arg > `--file` >
  STDIN.

## Acceptance criteria
- `python -m ector "I want a laptop for 150 usd"` prints valid JSON.
- `--lang fr` works end to end.
- Missing-model produces a clear, actionable error and non-zero exit.
