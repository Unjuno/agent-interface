# Supplemental parallel-branch STOP archive — Issue #4479

This directory is an exact snapshot of the 14-file subtree from remote branch
`research/needle-role-skill-robustness-3890-20260926`, tip
`bbfe2bb60d6c161d3a8dd6813754245f6e2068ad`. Its original tip is also preserved
by tag `archive/recovered/needle-role-skill-robustness-3890-original-20260926`.
The same-path files already on `main` were not overwritten; this snapshot is
isolated under `recovery/parallel_branch_stop_20260926/`.

## Disposition

This branch records a second, conflicting one-shot orchestration for allocation
`needle-role-skill-robustness-3890-v1`. Its STOP was before container creation:
the command invoked `docker --rm` without the `run` subcommand and exited 125.
No builder or loader completed; no seed was trained, and no scientific
measurement exists. The exact `STOP.json`, captured builder stdout, frozen
sources, and runner are retained unchanged here.

PR #4493 already preserves the distinct first STOP (missing `NEEDLE_SEED` and
`NEEDLE_OUTPUT`). Issue #4479 records that the parallel launch violated the
allocation's one-shot coordination boundary. These two STOPs remain separate
infrastructure/coordination evidence; do not pool them, relabel either as a
scientific FAIL, retry the allocation, or change PR #4493's result.

The original main-path source remains authoritative for PR #4493. This nested
snapshot is supplemental provenance only and is not a new runnable allocation.
No candidate, training, audit, or formal launcher was executed during recovery.
