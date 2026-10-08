# Issue #8589 T0 A01 — effect-aware selective recovery

This package tests one narrow method question from [Issue #8589](https://github.com/Unjuno/agent-interface/issues/8589): computational validity and external-effect replay eligibility are separate. The frozen candidate is an offline planner over a deterministic finite DAG; it has no effect executor.

Read [PROTOCOL.md](PROTOCOL.md) before interpreting the artifacts. `input.json` is candidate-visible; `truth.json` is auditor-only. `candidate.py` and `auditor.py` are separate implementations. `results/` contains the one formal candidate output and one independent audit. `REPORT.md` is the scoped result; `SHA256SUMS` binds package artifacts.

## Reproduction

Construction tests (not formal invocations):

```text
python -m unittest -v
python -O -m unittest -v
```

Formal candidate and auditor commands, immutable image identity, mount boundary, and no-retry count are recorded in `REPORT.md`. Do not rerun either formal command; a changed source or rerun requires a separately frozen successor allocation.
