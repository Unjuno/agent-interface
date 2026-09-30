# Issue #5346 T2 freeze — TTL-boundary successor

Status: preregistered after T1 was retained as `STOP_HARNESS_INVALID`.
T2 is a new allocation, not a retry. T1 source, raw, and first-audit output
remain unchanged under `stigmergy_5346_t1_successor/`.

## H/T/D/C/U

- **H:** Under a shared atomic admission gate, fresh scoped local markers can reduce redundant blocked proposals versus NONE while using fewer explicit coordination messages than central claims; marker hints stop suppressing proposals at the exact lease-expiry boundary. Markers never authorize admission.
- **T:** Exhaustively enumerate worker counts 2–4, every worker-order permutation, observation delays 0–4 ticks, marker conditions clean/lost/duplicated/stale/forged, and owner outcomes complete/crash. Compare NONE, CENTRAL_CLAIMS, LOCAL_MARKERS. Lease TTL=3, task duration=2, crash at tick 1; test delay/age at ticks 2, 3 (expiry equality), and 4. Use the same event order and atomic gate in all arms.
- **D:** PASS only if 1,600 schedules / 4,800 arm rows are complete; every completion follows an admitted lease/effect; no overlapping lease or unsafe admission occurs; the original crashed owner's release is exactly tick 3 (not task-duration tick 2); markers at age >=3 never suppress; lost/stale/forged/duplicated controls do not change the admitted-authority trace; every crash case recovers exactly once; local markers reduce blocked attempts versus NONE in at least one delayed-but-fresh stratum and use no more explicit messages than central claims; the independent auditor rejects both a release-time mutation and an authority mutation.
- **C:** This is a deterministic finite software model only. It does not establish strategic-agent behavior, live trace visibility, measured latency, or production safety. Central claims may reduce more blocked attempts while costing explicit messages; report the Pareto tradeoff, not a universal winner.
- **U:** Live trace observability/scope, strategic actors, clock skew, and realistic task-cost/latency distributions.

## Frozen protocol

Scenario order: worker counts 2, 3, 4; lexicographic worker permutations; delay 0, 1, 2, 3, 4; conditions `clean`, `lost`, `duplicated`, `stale`, `forged`; outcomes `complete`, `crash`. Arms are emitted in order NONE, CENTRAL_CLAIMS, LOCAL_MARKERS. One row per schedule-arm. A crash event at tick 1 does not revoke the lease: the original lease remains active until exactly tick 3. A fresh worker may acquire no earlier than tick 3; retry after expiry is tick 4. Task duration is 2 ticks. Marker age `>=3` is expired and cannot suppress a proposal. The gate ignores marker payloads.

The independent audit must parse raw only, reconstruct active lease intervals,
bind every `lease_release.tick` and `lease_grant.until` to the contract, compare
admitted grant/effect/completion traces across arms, reconstruct counts, and
run two negative controls in memory (TTL release mutation and marker-authority
mutation). Both must be rejected. The negative controls are audit self-tests,
not additional formal simulator invocations.

## Resource and no-retry boundary

No model, GUI, network, GPU, or external service. Python stdlib only, in the
locally cached image
`python:3.12-slim@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`.
One formal invocation in a fresh no-network container with read-only root,
1 CPU, 256 MiB, and 64 PIDs; run only after read-only Docker monitoring shows
no competing container. Preserve any nonzero or partial first outcome. No
retry or source edits after the formal invocation.

## Scope

Finite deterministic schedule evidence only. Synthetic delays and worker policy
are assigned, not measured. No result provides runtime authority, verifies a
real interface, or closes the project roadmap.
