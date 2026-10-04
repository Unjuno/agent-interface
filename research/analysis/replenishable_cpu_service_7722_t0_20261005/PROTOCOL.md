# #7722 T0 protocol — replenishable CPU service

Allocation: `CPU-CONTROL-7722-T0-20261005-01`. Frozen source base: `3dbbda05eb8d5067ee2c2969615e472a0f20f562`. Frozen candidates and cases are hash-bound in `freeze.json`; do not edit them after candidate launch.

## H / T / D / C / U

**H.** On each of three preregistered schedulable deterministic single-core traces, a control sporadic server with budget Qc=5 ticks per 1000-tick replenishment interval, combined with the same total rolling CPU allowance Q=100 ticks per interval, will reduce p99 cancel/release-service response by at least 20% versus both (1) priority-only dispatch over a shared Q=100 budget and (2) a shared queue with 64-job backpressure. It will remove every baseline deadline miss (deadline=100 ticks), complete no more than 10% fewer fixed-horizon best-effort jobs than priority-only, and expose every obligation. A negative control with no best-effort burst must keep reserved and shared p99 response within 5%. Overload and replenishment-boundary cases must remain explicit UNKNOWN/overload with obligations preserved.

**T.** One event-driven, integer-tick CPU-only simulation; 10 periods per trace, each 1000 ticks. The schedulable control offsets in `cases.json` are precomputed using CPython 3.11.9 `random.Random(seed).randint(400,600)` with one RNG instance per seed; the exact values are frozen, so the candidate does not draw randomness. 20 best-effort jobs of 5 ticks each arrive at each period boundary in schedulable cases. One control job of 4 ticks arrives per period at a frozen offset. Compare shared priority, shared queue with 64-entry admission backpressure, and server-reserved dispatch. Negative trace has no best-effort arrivals. Overload trace has two same-time control jobs against Qc=5. Boundary trace places obligations around a period boundary. Deadline is 100 ticks; finite horizon 10000 ticks. No live scheduler, GUI, model, input, GPU, memory pressure, network, or host configuration change.

**D.** `METHOD_PASS_SCOPED` requires an independent auditor to reconstruct every one-tick service event, job completion, rolling quota, obligation and summary from raw events; source/case hashes must match the frozen manifest; budget, deadline, missed-obligation, early-replenishment, uncharged-service and false-completion mutations must all be rejected. `H_PASS_SCOPED` additionally requires all per-trace response, deadline, best-effort-loss, negative-control and overload criteria above. Any other outcome is retained as FAIL/HOLD; no tuning or candidate rerun.

**C.** A shared queue may already have sufficient headroom; the small synthetic budget/arrival envelope may exaggerate contention; backpressure may be equivalent when its queue bound does not activate; CPU dispatch may not explain real release delay.

**U.** This deterministic model establishes only arithmetic and policy behavior under the exact frozen tick model. It does not show WSL/Linux cgroup enforcement, host scheduler behavior, OS/backend acknowledgement, physical release, real WCET, end-to-end safety, or that CPU contention explains Issue #59. WSLc CPU/memory flags are requests, not enforcement evidence. No hard-real-time claim follows.

## Frozen units and policy

| Symbol | Meaning | Unit/type | Frozen value |
|---|---|---|---:|
| t | Simulated monotonic event time | tick, integer | 0–9999 |
| P | Rolling replenishment window | tick, integer | 1000 |
| Q | Total shared CPU allowance per rolling window | service tick, integer | 100 |
| Qc | Sporadic control-service allowance per rolling window | service tick, integer | 5 |
| Qb | Reserved-policy best-effort allowance per rolling window | service tick, integer | 95 |
| Wc | Cancel/release bookkeeping service per job | service tick, integer | 4 |
| Wb | Best-effort verifier/capture job service | service tick, integer | 5 |
| d | Control completion deadline from arrival | tick, integer | 100 |
| H | Fixed trace horizon | tick, integer | 10000 |

Each tick of execution at t contributes one unit to the relevant trailing half-open window `[t-P,t+1)`; a tick exactly P in the past has replenished. Priority dispatch always selects an arrived control obligation before best-effort work. Reserved dispatch additionally enforces Qc and Qb=Q-Qc using the same trailing-window rule. The backpressure comparator rejects best-effort arrivals only if its bounded 64-job queue is full; it does not reserve CPU tokens or discard control obligations. Ties are FIFO, then job identifier. Service is nonpreemptive only at one-tick granularity.

## Execution record

Candidate and auditor each run once in separate fresh, network-disabled WSLc containers with cached image `python@sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016`, requested `--cpus 1`; package input is read-only and output is written to dedicated host directories. No pull, retries, GPU, shared-container modification, or cleanup of pre-existing objects. Preserve exact stdout/stderr, exit status, wall time, WSLc version, image identity and any cgroup/swap warning. Requested resource flags do not establish enforcement.
