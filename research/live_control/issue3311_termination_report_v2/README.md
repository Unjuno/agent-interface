# Issue #3311 termination report contract — successor v2

This package is a CPU-only diagnostic/support contract for preserving a
machine-readable outcome when a future integrated-efficiency runner exits
before it has a complete trace and independently audited report. It does not
modify the frozen v1 runner or its result tree.

`supervisor.py` verifies source pins before launch, runs one child runner and
one auditor in a fresh allocation directory, and emits an append-only
`TERMINATION_REPORT.json` on STOP/HOLD conditions. `audit_termination_report.py`
is a separate raw-file auditor; it recomputes every listed artifact digest and
rejects path escape or disposition confusion. Child exit codes and exception
text never imply REJECT. A successfully audited scientific RETAIN/HOLD/REJECT
report is left unchanged.

The hypothesis, bounded test, controls, decision, and limitations are frozen in
`PLAN.md` and `FREEZE.json`. This successor corrects the repository-root
resolution defect in both predecessor entrypoints and pins the evaluator/runner
blobs at the current main commit. The one-shot local entrypoint retains its
stdout/stderr, per-case artifacts, and `RESULT.json` under `results/local-02/`.
The predecessor STOP remains in allocation 01 and is not overwritten.

The supervisor cannot report if it or the operating system is forcibly stopped
before writing. A future allocation must integrate this package into a new
runner, use a new source freeze and fresh output directory, then independently
audit the terminal record. This package alone does not satisfy #3311's live
cold/warm/invalidation/repair comparison.
