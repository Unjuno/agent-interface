# #6613 successor allocation A01

This is a new, narrow allocation after the predecessor's `STOP_PREREGISTRATION_HASH_MISMATCH`. That STOP and its branch are immutable. It addresses the residual explicitly not exercised by #6347: variable service durations and per-request deadline completion under repeated contention. #6347's simultaneous-intent, delay-swap, batch-boundary, and repeated-window results are not pooled or rerun.

## H / T / D / C / U

**H.** On identical finite, already-authorized, same-priority task traces with a single exclusive GUI-resource abstraction, least-service-debt scheduling reduces worst eligible wait relative to FIFO and shortest-service-first under recurring asymmetric arrivals, without reducing independently scored on-time completions below the fixed floor, suppressing mandatory interrupts, or dispatching revoked/ineligible work. This can fail; simple baselines may match or win.

**T.** Thirty-two held-out seeds (10000–10031) × three strata: recurring asymmetric arrivals, a two-wave burst/recovery trace, and a revoked-principal plus mandatory-interrupt control; six requests per A/B principal per trace. Xorshift32-v1, arrival/service/deadline transforms and stratum constants are embodied separately in candidate and auditor and held fixed. Candidate compares FIFO, shortest-service-first, and service-debt/rotating-tie scheduling on identical input rows. One virtual single server; integer ticks; no model, GUI, user data, external effects, or real authorization. Candidate and independent raw-only auditor are run once each in separate containers after this freeze. No retries or tuning. The auditor independently replays inputs and schedules.

**D.** `PASS_METHOD_SCOPED` only if all 288 policy-trace rows are independently reconstructed, every task is accounted for once, no ineligible task dispatches, mandatory work bypasses optional requests when both are ready, and service-debt lowers the across-seed mean of per-trace worst eligible wait versus both baselines in the asymmetric stratum while its aggregate on-time optional completions are no lower than the weaker baseline in each stratum. Any safety/accounting violation is `FAIL_METHOD`; absent wait improvement or an on-time floor miss is `FAIL_HYPOTHESIS`. This is synthetic scheduler method evidence only.

**C.** Alternative baselines, arrival ties, finite horizons, and service-cost accounting may dominate; a fixed priority/FIFO contract may be more appropriate than fairness.

**U.** No human principal, application, authority system, actual GUI service-time estimate, real deadline value, deployed fairness, task benefit, safety or product claim follows. Service debt only orders requests already independently marked eligible; it grants no access.

## Frozen execution

Main/source: `aec152dca5d9a28d916761421a74c703600df683`. Allocation: `LONG-HORIZON-SERVICE-DEBT-6613-ORB-A01-20261002-01`. Branch: `research/service-debt-deadline-6613-orbstack-a01-20261002`. Additive path: this directory. Image: `python:3.12-slim@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f` (`linux/arm64`), pull never, network none, read-only root and source, 1 CPU, 256 MiB, 64 PIDs, dropped capabilities, no-new-privileges. Candidate/auditor each execute in a fresh container; outputs use a separate writable host directory. Existing containers are not touched. Memory limits are configuration only unless the runtime reports effective enforcement.

Construction checkpoint: the initial hand-authored three-trace construction failed to discriminate (debt's worst wait 8 ticks vs baseline 7 on the asymmetric trace). It is not the formal input. Formal held-out seeds 10000–10031 were fixed, not selected by searching for favorable outputs.

The formal fixture, candidate, auditor and test source are frozen by the allocation commit before either formal invocation. Candidate writes the complete raw policy schedules. Auditor consumes only fixture and raw file; it does not import candidate code. Each is allowed one invocation; any nonzero exit or evidence anomaly is retained as STOP/FAIL, with zero retries.
