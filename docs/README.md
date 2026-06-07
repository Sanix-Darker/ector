# ECTOR Documentation

This directory contains the full planning, audit, design, and testing
documentation for the **ECTOR** project (Extract eCommerce products and budget
from free text using NLP).

The documentation is intentionally split into small, focused files so each
concern can be read, reviewed, and maintained independently.

## Index

### Foundations
- [`01-overview.md`](./01-overview.md) — What ECTOR is, its purpose and scope.
- [`02-architecture.md`](./02-architecture.md) — Current vs. target architecture.
- [`03-glossary.md`](./03-glossary.md) — Domain & NLP terminology used across docs.

### Audit (what is wrong today)
- [`audit/01-bug-catalog.md`](./audit/01-bug-catalog.md) — Every confirmed bug with
  reproduction steps, root cause, and the fix.
- [`audit/02-code-smells.md`](./audit/02-code-smells.md) — Maintainability and
  optimization issues that are not strictly bugs.
- [`audit/03-correctness-risks.md`](./audit/03-correctness-risks.md) — Heuristic
  accuracy risks and false-positive/negative analysis.

### Features (capabilities, current and planned)
- [`features/01-product-extraction.md`](./features/01-product-extraction.md)
- [`features/02-budget-detection.md`](./features/02-budget-detection.md)
- [`features/03-currency-and-price-parsing.md`](./features/03-currency-and-price-parsing.md)
- [`features/04-multilingual-support.md`](./features/04-multilingual-support.md)
- [`features/05-model-management-and-caching.md`](./features/05-model-management-and-caching.md)
- [`features/06-public-api.md`](./features/06-public-api.md)
- [`features/07-cli.md`](./features/07-cli.md) — Planned (missing today).
- [`features/08-typo-tolerance.md`](./features/08-typo-tolerance.md) — Fuzzy
  normalization + parse-independent fallback for messy/typo input.
- [`features/09-structured-fields.md`](./features/09-structured-fields.md) —
  brand, attributes, condition, price constraints, intent.

### Fixes (concrete remediation plans)
- [`fixes/01-fix-plan.md`](./fixes/01-fix-plan.md) — Mapping of each bug to a fix task.

### Plan (how we get there)
- [`plan/01-roadmap.md`](./plan/01-roadmap.md) — Phased delivery roadmap.
- [`plan/02-micro-plan.md`](./plan/02-micro-plan.md) — Extremely detailed,
  step-by-step execution plan with verification gates.
- [`plan/03-refactor-plan.md`](./plan/03-refactor-plan.md) — Module split and
  target package layout.
- [`plan/04-implementation-status.md`](./plan/04-implementation-status.md) —
  Final delivered state, module map, and behavioral changes.

### Testing
- [`testing/01-test-strategy.md`](./testing/01-test-strategy.md)
- [`testing/02-test-matrix.md`](./testing/02-test-matrix.md)

## How to read this

If you are new to the project, read `01-overview.md` then `02-architecture.md`.
If you are here to fix or extend the code, read the audit folder and
`plan/02-micro-plan.md`. The micro-plan is the source of truth for execution
order and verification gates.
