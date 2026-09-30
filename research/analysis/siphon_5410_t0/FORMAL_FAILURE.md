# Formal T0 failure — Issue #5410 bounded resource simulator

Issue: [#5410](https://github.com/Unjuno/agent-interface/issues/5410)
Task: `ISSUE-5410-SIPHON-T0-20260930`
Disposition: `FAIL_PREREGISTERED_TIMED_LIVENESS_GATE`

## Failure decision

The visible opposed-order case supports the structural-cycle hypothesis: NAIVE deadlocks with only two workflows complete; SCC_GUARD detects one cycle, rolls back/replans, and completes all four in 6 virtual ticks; SAFE_REACHABILITY completes all four in 5 ticks; GLOBAL_EXCLUSIVE completes all four in 8 ticks. However, the preregistered fault matrix required no unrecovered deadlocks under the lease-expiry case. All four policies leave beta incomplete at the 40-tick bound; SCC_GUARD and SAFE_REACHABILITY each repeatedly expire/reacquire and never finish. The primary D gate therefore **FAILS**, despite positive results in the opposed-order and independent-work scenarios.

The exact counterexample is a beta lease of 2 ticks with a two-resource plan plus a completion step. After canonical replan the policy still needs more than two ticks from first acquisition to release. The reachability check tests resource completion order but does not include lease deadline feasibility. Releasing/retrying cannot fix a lease whose allowed lifetime is shorter than the critical path; retries create livelock. The retained run records 12 expiries each for SCC_GUARD and SAFE_REACHABILITY. This is a model/policy failure, not a Docker or infrastructure failure.

## H/T/D/C/U

- **H:** A prospective SCC guard can prevent visible wait cycles while preserving concurrent independent work, but it must also respect timed resource/lease constraints to prevent starvation.
- **T:** One deterministic OrbStack container run over five unit-capacity resources, four workflows, seven schedules/fault cases, and four policies (28 runs). The schedules include opposed order, lease expiry, cancellation, authority revocation, hidden dependency, guard retry/backoff, and independent workflows.
- **D:** **FAIL** because the preregistered zero-unrecovered-deadlock gate fails in `lease_expiry_recovery` for every policy, including the reachability comparator. This is not relabeled UNCERTAIN: the raw trace establishes repeated expiry/reacquisition and no completion by tick 40. Trace ownership/release/terminal accounting had no independent integrity errors. Four corrupted copies were rejected.
- **C:** If a lease covers the complete workflow critical path or can be renewed safely, reactive SCC prevention may be useful; a fixed global order prevents structural cycles but does not repair an infeasible lease budget. Timed safe-state admission may be needed before ranking the policies.
- **U:** Discrete-event timing and leases are authored; the simulator omits GUI/tool latencies, hidden real effects, scheduler jitter, and lease-renewal authority. The outcome is scoped to this finite model and does not establish production deadlocks or safety.

## Results

| scenario | NAIVE | GLOBAL_EXCLUSIVE | SCC_GUARD | SAFE_REACHABILITY |
|---|---|---|---|---|
| opposed order | 2/4 complete, deadlock, 4 ticks | 4/4, 8 ticks | 4/4, 6 ticks, one rollback | 4/4, 5 ticks, one oracle denial |
| lease expiry | 3/4, unrecovered by 40 ticks, 13 expiries | 3/4, unrecovered by 40, 11 expiries | 3/4, unrecovered by 40, 12 expiries | 3/4, unrecovered by 40, 12 expiries |
| cancellation | 3/4 and one cancelled, 3 ticks | 3/4 and one cancelled, 6 ticks | 3/4 and one cancelled, 3 ticks | 3/4 and one cancelled, 3 ticks |
| authority revocation | 3/4 and one revoked, 3 ticks | 3/4 and one revoked, 7 ticks | 3/4 and one revoked, 3 ticks | 3/4 and one revoked, 4 ticks |
| hidden dependency | 2/4, deadlock | 3/4, one explicit UNKNOWN | 3/4, one explicit UNKNOWN | 4/4 with complete hidden model |
| retry/backoff | 2/4, deadlock | 4/4, 8 ticks | 4/4, 6 ticks | 4/4, 5 ticks |
| independent workflows | 4/4, 3 ticks | 4/4, 6 ticks | 4/4, 3 ticks | 4/4, 3 ticks |

All detailed event histories are retained in `raw/formal.json`; the compact 28-row rollup is `raw/summary.json`. A return of `UNKNOWN` under an incomplete graph is not treated as an unsafe admission. The reachability comparator's access to the full hidden dependency is an oracle advantage, not a fair runtime-information assumption.

## Frozen execution and audit

Issue #5410 preregistration: comment `5911036464`.

- Frozen main base: `6a1e2f16762b1a2ace7347a282f7ad6d12c7a0fe`.
- Command: `docker run --rm --network none -v "$PWD/research/analysis/siphon_5410_t0:/work" python:3.12-slim sh -c 'python /work/experiment.py > /work/raw/formal.json'`.
- Engine: OrbStack Docker `29.4.0`, `linux/arm64`.
- Image ID/digest: `sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`.
- Formal candidate invocations: 1; no RNG, retry, or tuning.
- Independent auditor reproduced 28 rows, checked per-resource ownership and release traces, and returned FAIL only for the preregistered guarded-policy deadlock condition in lease expiry.
- Corruption controls: 4/4 mutated copies rejected; the added mismatch errors identify each mutation.

## Artifact hashes

| artifact | SHA-256 |
|---|---|
| `experiment.py` | `a136e0f92591140220c8d0d8f8ba2cdaf0456947b5f9f9e7838a6a0bb17e9e9a` |
| `audit.py` | `220ff8b1145f5487047406dc1837e172f0f633c6bcec6fc5ae5abebf0086dcdb` |
| `corruption_controls.py` | `2ed2faaab53925d6b505e63dcdc3ef164d00c419d85965c58f7db58869943f41` |
| `raw/formal.json` | `037bfafc94bc7dc01a8e311d30bf06eaabf0dec4be734d658fd99273ae87dada` |
| `raw/audit.json` | `02ba6475e7f23eb5896ef91a50aed90e672d3a87d190a931055f18dcb8a56381` |
| `raw/corruption_controls.json` | `6333e6d3dcc3748dccab09a8b210da552380c983497cab48c681c05d28aae6ba` |
| `raw/summary.json` | `7cc1d00746b7ead0c8f75215528a8001f1b707b2fd74d1311296074b3ac0a2d5` |

## Stop and next boundary

Stop this frozen T0. Do not lengthen leases or change the simulator after seeing the formal result and rerun it under the same allocation. A successor experiment may separately preregister lease-aware admission: model minimum completion-time/reservation feasibility and bounded renewal, then compare the revised gate on a fresh allocation. Preserve this T0 failure unchanged.
