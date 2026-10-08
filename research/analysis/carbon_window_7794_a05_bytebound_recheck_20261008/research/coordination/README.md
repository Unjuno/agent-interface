# Coordination research

This directory contains research on coordination semantics such as claims, leases, barriers, generations, ownership, readback, revocation, durable state, and concurrent actors.

It is **research evidence**, distinct from the operational orchestration records in [`../orchestration/`](../orchestration/) and [`../../docs/orchestration/`](../../docs/orchestration/).

## Interpretation

- Child directories are scoped experiments, not repository administration state.
- Use [`../../RESEARCH.md`](../../RESEARCH.md) for scientific status and claims.
- Use [`../../docs/CURRENT_GOAL.md`](../../docs/CURRENT_GOAL.md) for the active project direction.
- Preserve exact evidence paths when reorganizing; add indexes instead of renaming retained experiment directories casually.

## Issue #5346 — stigmergic coordination

- [T1 — STOP_HARNESS_INVALID](stigmergy_5346_t1_successor/REPORT.md): the one-shot formal allocation released a crashed owner's lease at task-duration tick 2 instead of frozen TTL 3. Preserve its raw and first audit, but do not interpret its apparent policy metrics.
- [T2 — scoped TTL-boundary PASS](stigmergy_5346_t2_successor/REPORT.md): 1,600 deterministic schedules; authority traces stayed identical while fresh local markers reduced blocked proposals, with explicit central-message and live-transfer limitations.
