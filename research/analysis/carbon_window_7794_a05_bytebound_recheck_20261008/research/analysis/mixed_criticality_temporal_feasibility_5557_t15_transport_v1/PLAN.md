# Issue #5557 T15-03 — bounded source transport and temporal feasibility

## Objective and lineage

This fresh allocation tests the same finite temporal-feasibility hypothesis as T15-01/02, which both stopped before source/tests/candidate execution. It is not a retry: the source-delivery mechanism is changed to avoid the stalled `actions/checkout` archive path, while the synthetic workload, candidate, independent reconstruction, digest-pinned container, and scientific decision rule remain fixed. Prior allocations and evidence are preserved unchanged.

Frozen main: `d54d0722195f6fb86158f259ed80754ba046ddea`. Issue hypothesis/workload: comments #5918821974 and #5918873465. Allocation: `ISSUE-5557-TEMPORAL-SERVICE-T15-20261001-03`. Exact source manifest, workflow digest, and this allocation's start gate must be recorded in an Issue comment before opening the PR that triggers execution.

## H/T/D/C/U

- **H:** Per-tick HI deadline and observer max-gap enforcement exposes temporal infeasibility despite horizon-wide aggregate headroom, while feasible traces retain the LO minimum.
- **T:** One newly opened same-repository PR triggers exactly one job in `python:3.12-slim@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`. No checkout action is used. Fetch only the frozen package from `raw.githubusercontent.com` at the exact PR head, with 30-second total and 6-second per-request deadlines. Verify the preregistered manifest digest, then every payload SHA-256, and the allocation/image fields before executing any fetched Python. If the canary misses its deadline or any byte/hash/provenance check fails, STOP with candidate=0, auditor=0. Otherwise run one construction-test command, candidate once, and raw-only auditor once, sequentially; upload exact outputs. The workflow runs on `pull_request.opened` only, not synchronize/report updates.
- **D:** `PASS_TEMPORAL_SERVICE_CONTRACT_SCOPED` only when all 32 rows match independent reconstruction, temporal SAT/UNSAT and contract guarantees hold, the capacity-3/three-HI control remains feasible, and all three corruption controls are rejected. Any scientific contract mismatch is FAIL; fetch, provenance, container, or independent-audit failure is STOP. Candidate and auditor counts must each equal exactly one for a scientific decision.
- **C:** Compare aggregate-total and HI-priority baseline against the temporal contract decision; a horizon-total model could be sufficient only where service is temporally fungible.
- **U:** Hand-authored binary arrivals, one resource, four ticks, deterministic service; no live workload distribution, semantic observation utility, general schedulability proof, production safety, or product-benefit claim.

## Fixed model

Four ticks; exhaustively enumerate 16 binary HI-arrival vectors at capacities 2 and 3 (32 rows). Each active HI release requires 2 units immediately. `RECOVERY_OBSERVER` requires 1 unit each tick (max gap 1, including initial tick 0). `LO_PLANNER` minimum is 1 total unit. Capacity 2 creates the aggregate-feasible but same-tick HI+observer conflict; capacity 3 supports up to three HI releases while retaining the planner minimum, and four HI releases are UNSAT.

Candidate and auditor bytes are copied unchanged from the T15-02 frozen package; their individual digests are in `SHA256SUMS.txt`. The auditor reconstructs rows without importing candidate code. Mutations: false SAT on temporal conflict, omitted required observation, silently dropped planner minimum.

## Run protocol and limits

Formal outputs belong under `results/formal-03/`. A result is not established by transport canary or construction tests alone. Preserve Actions logs and raw/audit artifact bytes exactly. This allocation has no retry; a failed canary consumes T15-03 as infrastructure STOP and any later attempt requires a new Issue preregistration. Never use host Python as a substitute for the allocated container experiment. OrbStack was unresponsive at T15-03 preparation time.
