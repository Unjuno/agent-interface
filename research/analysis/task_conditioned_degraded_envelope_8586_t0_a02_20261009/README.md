# TDCE T0 A02 — Issue #8586

This additive successor tests a second distinct joint-loss interaction while preserving A01 unchanged. It exhaustively enumerates 336 task-local states over four authored task classes and six contexts. The frozen candidate ran once; the raw-only independent auditor ran once and returned `PASS_METHOD_SCOPED` with zero errors.

The result contains two distinct two-capability joint-loss configurations where edge-by-edge composition continues without satisfying the full task obligations. The task-conditioned envelope has zero false continuations and zero false stops across the authored feasible rows; blanket stop rejects 36 feasible rows.

This is finite authored-model evidence only. It does not show that these failures occur in a deployed interface, validate any real route proof, or establish live control, safety, latency, reliability, or product benefit. A01 and A02 are not pooled.

See [protocol](PROTOCOL.md), [freeze](FREEZE.json), [model](model.json), [candidate](candidate.py), [independent auditor](auditor.py), [run record](RUN_RECORD.json), [report](REPORT.md), and retained [raw/audit outputs](results/).
