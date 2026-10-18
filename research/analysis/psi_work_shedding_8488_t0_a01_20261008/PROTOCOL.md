# Issue #8488 — PSI-triggered work shedding, T0 A01

## H / T / D / C / U

- **H (hypothesis):** in the authored finite workload below, a two-window memory-PSI trigger suspending optional work before fresh mandatory arrivals reduces mandatory deadline misses relative to fixed concurrency, while preserving every mandatory obligation and its evidence. A queue-only trigger reacts too late in the primary trace.
- **T (test):** run the frozen deterministic 16-tick, 1-second/tick event model once for four policies × eight declared traces. Candidate and independent auditor compute the same outputs separately. The only measured outcomes are within-model completion/deadline/miss/defer/transitions and evidence accounting.
- **D (decision):** `PASS_METHOD_SCOPED` only if (i) PSI policy has strictly fewer primary-trace mandatory deadline misses than fixed and queue policies; (ii) it has zero primary mandatory deadline misses; (iii) short spike, unrelated CPU/I/O, and unavailable-PSI controls do not trigger PSI shedding; (iv) no mandatory job is dropped or falsely reported completed; (v) all four adversarial mutations are rejected. Otherwise report the precise FAIL/HOLD; no post-freeze tuning.
- **C (controls):** delayed signal, single-window spike, unrelated CPU/I/O pressure, unavailable signal (must stay UNKNOWN), low-free-memory/no-stall, pressure recovery with mandatory backlog, and repeated isolated spikes; paired fixed/queue/free-memory/PSI policy runs over identical traces.
- **U (uncertainty):** authored synthetic trace, service durations, pressure-to-capacity relation and thresholds are not empirical. This is not Linux PSI behavior, operating-system scheduling, container, model, application, deadline-SLO, causal, or deployment evidence. No live/resource-changing test is authorized.

## Frozen semantics

The tick is one second. Jobs arrive at the start of their tick. A worker executes one integer service unit per tick; mandatory jobs are non-preemptive after start. Two workers are available absent modeled pressure; the authored pressure booleans reduce capacity to one. Jobs are chosen by earliest deadline, then stable ID; jobs without deadlines sort last. `deadline` is an exclusive completion bound: a job still incomplete at the end of tick `deadline` is a miss. Mandatory classes are `mandatory_verify`, `freshness_observation`, and `mandatory_release`; optional classes are `speculative` and `reconstructible_cache`. Shedding suspends optional jobs, including already-started ones, releasing their worker slot while preserving exact remaining service and evidence ID; resumed jobs continue that remaining service. PSI observations are delayed by the trace's fixed nonnegative offset, clamped to its first sample; null remains UNKNOWN. PSI entry uses >=150ms in the prior 1-second window for two consecutive observations; exit uses <=50ms for two observations, 3-tick cooldown, and zero waiting mandatory jobs. These are synthetic choices, not operational settings.

The primary contrast is the same frozen `memory_burst_primary` trace under all policies. Evidence IDs include each tick's `RAW-*` observation ID and each job's `E-*` obligation evidence. Incomplete mandatory release is `UNKNOWN`, never `RELEASED`. Candidate output and independent reconstruction are compared as complete canonical JSON structures.

## Formal sequence

1. Run construction-only tests and static/syntax checks. Repair only before freeze.
2. Freeze protocol, input, candidate, auditor and tests by SHA-256. Record main base and environment/precheck.
3. Invoke candidate once and preserve its raw JSON and process status.
4. Invoke independent auditor once against that exact output. Do not regenerate/retry on formal failure; preserve failure and require a distinct successor allocation for repairs.
5. Test mutations against the frozen output/auditor logic without rerunning candidate: (a) swap the early/late PSI signal ordering while retaining outcomes; (b) alter an event intensity; (c) swap trace/policy labels; (d) pool/omit a trace result to hide the primary policy contrast. Each must be rejected by a dedicated integrity/contrast gate.

This allocation performs no process-wide PSI access and changes no host/container resources. Container preflight failed due an OrbStack content-store `operation not supported` error; therefore no container-isolation claim is made.
