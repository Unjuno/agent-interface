# Measurement research

This directory contains scoped measurement, composition, timing, currentness, authority, readiness, concurrency, and related formal/controlled experiments.

Each child directory is an evidence unit, not a release or automatically promoted component. Typical contents include a frozen plan/source, candidate/oracle code, formal result, audit, corruption controls, and a report.

## Reading order

1. Start with the top-level [`../../RESEARCH.md`](../../RESEARCH.md) for the project evidence ledger.
2. Use the linked Issue/PR or a child experiment's `REPORT.md` / `PLAN.md` to determine scope.
3. Treat PASS/FAIL/HOLD/STOP as scoped to the experiment's declared H/T/D/C/U and environment.
4. Do not infer runtime or product support from a measurement directory alone.

The large number of child directories is intentional retained evidence. Repository cleanup should add navigation or archival explanation rather than merge/rename completed evidence paths without a provenance-preserving reason.
