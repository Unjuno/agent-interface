# Allocation 02 — preparation note

Issue #6442, successor to #5756. This package is additive to the preserved allocation-01 STOP; do not edit its `FREEZE.json`, `SHA256SUMS`, `STOP.json`, `STOP.md`, or PR #6456 evidence.

## Protocol correction

The authored 32-fixture development simulation gives partial/revision successes `stateless=16/16`, `hard=0/16`, `soft=16/16`, `exhaustive=0/16`. This supports only the preregistered finite contrast against hard same-epoch exclusion; the no-memory stateless baseline ties soft. No unique soft-bias advantage or causal attribution is established. The independent audit therefore emits all four strata scores and all three soft-minus-baseline contrasts, and the report must state the tie plainly.

The local construction suite is 13/13 (5 policy tests, 8 auditor tests including one all-row valid audit; six mutation-rejection controls). This is host development evidence only, not the fresh WSLc construction run for allocation 02. Allocation-01's one WSLc construction run remains unchanged; allocation-02 permits one construction run, one candidate run, and one independent audit, with no retry.

## Current disposition

The package is prepared against the exact `base_main_sha` in `FREEZE_A2.json`. The exact shared WSLc host is used by another active owner preparing Issue #6477. Their most recent containers are exited, but explicit lane release is pending. Therefore `STOP_SHARED_WSLc_OWNER_ACTIVE`: candidate=0, auditor=0, and allocation-02 construction container=0. Do not infer clearance from idle GPU, exited containers, or CPU snapshots.

The WSLc start gate must be rechecked immediately before use: current main equals frozen base; source/image/output hashes match; no competing WSLc owner; explicit owner release is received; pinned image already exists; fresh output directory is empty. In the actual construction container, print and retain `/sys/fs/cgroup/memory.max` alongside the tests. A positive `memory.max` check may establish the memory ceiling even if swap-controller warnings remain; do not claim a swap cap unless separately observed.

No candidate, independent audit, scientific result, main merge, or product claim is made by this preparation note.
