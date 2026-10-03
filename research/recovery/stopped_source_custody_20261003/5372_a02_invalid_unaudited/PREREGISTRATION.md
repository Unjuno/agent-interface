# #5372 priority-only, retry pressure, and fairness A02 preregistration

Status: construction candidate only; no formal candidate/auditor invocation yet.

## H / T / D / C / U

- **H:** Under a fixed two-class open-loop offer stream above one verifier's capacity, priority-only scheduling cannot prevent retry-created queue work and can starve low-priority offers. A downstream retry-admission gate should suppress amplification; an age-based service override should recover some low-priority completions without missing mandatory safety-lane events.
- **T:** Twelve ticks each offer one HIGH and one LOW task (24 offers fixed across arms). A single normal verifier serves one job/tick. An unfinished task becomes retry-eligible at age 2. Compare FIFO with open retry admission, priority-only with open retry admission, priority-only plus retry suppression at queue depth 4, and the same pressure gate plus a 3-tick LOW-job aging override. Horizon 12; freshness threshold 4 ticks. Four mandatory safety events at ticks 1/4/7/10 use an isolated one-tick lane with deadline 1. Preserve all offers, job events, retries/suppressions, cancellations, stale/fresh/UNKNOWN outcomes, per-class completions, and safety events. Construction uses host tests; formal candidate and independent raw-only audit run at most once each in separate WSLc CPU containers, cached digest-pinned image, pull never, network none, 1 CPU, requested 256 MiB; retry 0. Recheck resource availability before either formal launch.
- **D:** PASS_METHOD_SCOPED only if independent event replay exactly matches every offer and event; the pressure gate reduces retry jobs and does not increase peak backlog vs priority-only; the aging arm increases LOW verified count over pressure-priority; all mandatory safety events meet deadline; all frozen corruption controls are rejected. This is a finite mechanism test, not an asymptotic stability proof.
- **C:** The gate is a fixed queue-depth threshold and one-shot retry rule. A different arrival mix, arrival uncertainty, capacity, priority weights, or retry hazard can reverse the comparison; service aging may lower urgent HIGH throughput.
- **U:** An authored deterministic discrete-event fixture only. It cannot establish stationary stability, real system queue behavior, calibrated freshness, human benefit, or product safety. A finite horizon cannot prove bounded backlog under unbounded time.

## Novelty and separation

This is distinct from #5372's prior fixed-load FIFO/backpressure comparison and A01's route-set expansion test. A01 compares base/expanded route work; this allocation holds the route set fixed and tests priority-only scheduling, retry admission, and an explicit low-priority fairness override. It does not rerun or alter earlier results.

## Invocation contract

No formal run is allowed until source and fixture hashes are frozen, local construction tests pass, the current-main priority check is repeated, the image digest is verified in the intended WSLc session, output paths are absent, and no conflicting WSLc workload is active. If any gate fails, retain a pre-run STOP and do not retry this allocation.

