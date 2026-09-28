# Issue #5126 lineage counterexample recheck — H/T/D/C/U

## H

The exact whitespace-only lineage mutation identified after #1839 v1 is still
accepted by the merged v1 candidate, oracle and raw-only auditor on current
main. The currently published physical/scorer schemas may also lack distinct
source-record IDs needed to reject duplicated source events; if so, v2 must
hold rather than invent identities.

## T

Pin current main, the immutable #1839 v1 result, candidate, oracle, auditor and
reproducer hashes. On a disposable in-memory copy, replace session, plan,
actuation, owner and effect IDs with a single whitespace-only value. Run both
v1 classifiers and the independent raw audit against that copy. Do not write
inside the historical v1 directory. Then inspect current source schemas for
explicit event identity/sequence fields. This is a host-only construction
recheck; formal v2 cases require the explicitly assigned offline-container
slot before execution.

## D

`CONFIRMED_LINEAGE_ACCEPTANCE` if all three v1 components still accept the
mutant. `NOT_REPRODUCED` if any rejects it. Separately report whether current
source fields support unique source-event references. No positive v2 contract
claim follows from this probe.

## C

The mutation is post-outcome and synthetic. It cannot establish live event
availability, clock calibration, physical timing, task efficacy or model value.
No runtime/controller code, historical output, GPU, container, X11, model, or
input is touched.

## U

The successor's strict positive/negative contract and independent corruption
audit remain untested here. This construction cannot be merged as a resolved
#5126 result.

## Frozen source identities

See `FREEZE.json`; this file and the reproducer are frozen before the one
construction invocation. The exact command and output are in `EXECUTION.json`.
