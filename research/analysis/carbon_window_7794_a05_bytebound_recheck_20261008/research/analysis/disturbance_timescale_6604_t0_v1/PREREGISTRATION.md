# Preregistration — Issue #6604 T0

Allocation: `DISTURBANCE-TIMESCALE-6604-T0-ORBSTACK-20261002-01`  
Frozen main: `2c92d3979d5cdbeadef1fb1225ac9f60a206035c`  
Branch: `research/disturbance-timescale-6604-t0-orbstack-20261002`  
Path: `research/analysis/disturbance_timescale_6604_t0_v1/`

## H / T / D / C / U

**H:** In this finite plant fixture, the direct and fixed local-periodic laws have a route-ranking crossover between slow drift and fast reversal, while a predeclared no-crossover pair does not. Pooled scoring may select a route that is worse in one declared stratum. No real route claim follows.

**T:** Seven schedules × two fixed arms = 14 candidate rows, horizon 12 ticks each. Plant state starts at 0, clamps to [-24,24], and each tick admits exactly one command per arm with magnitude capped at 2. Direct samples its visible numeric target at ticks 0,3,6,9 and applies the command immediately. Local-periodic samples each tick and applies each command one tick later. At termination, direct is neutral at tick 12; local-periodic applies its one queued command and becomes neutral at tick 13. Both use identical numeric action vocabulary, number of command opportunities, horizon, plant, and scorer. Candidate sees only `cases.json`; `oracle.json` is scorer-only. The semantic-swap case is intentionally observationally identical to the slow schedule but its meaning changes at tick 6 without a cue; no semantic-effect claim is admissible.

Schedules: planted slow drift; planted alternating fast reversal; null slow drift; null medium drift; abrupt target step; no-motion; and unobservable semantic swap. Primary score is per-tick absolute numeric tracking error plus the terminal-release phase error. Hard gates: every arm has 12 command rows; applied input within cap; position within limits; explicit neutral receipt; exact source-order and timestamp accounting.

**D:** `PASS_METHOD_SCOPED` only if the independent replay agrees on every raw row, local wins slow and direct wins fast in the planted matrix, both no-crossover cases have the same route ordering, the pooled matrix is reported alongside per-stratum outcomes, all safety/release/action-budget gates pass, and no semantic claim is emitted for the unobservable swap. Otherwise retain exact `FAIL_INTEGRITY`, `FAIL_SAFETY`, or `HOLD` with raw first outcome; no retries.

**C:** Results may be entirely determined by the authored schedules and fixed one-/three-tick observation cadence. A universal simple route may dominate supported real workloads; route cost, useful feedback and task success are absent.

**U:** No GUI, DOOM, human, model, actual actuator, real release, runtime, latency distribution, broad safety, human-tempo or product-benefit inference. T0 is a finite simulator/method test only.

## Frozen source identities

See `FREEZE.json` for source SHA-256 values. Image is cached locally as `python:3.12-slim`, RepoDigest `python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`, image ID with the same digest, `linux/arm64`. No pull/build.

## Formal one-shot commands (not yet run)

1. Candidate once in OrbStack with `--pull=never --network=none --cpus=0.25 --memory=512m --pids-limit=64 --read-only`; mount source read-only and only its unique raw-output directory writable.
2. If and only if candidate exits 0, independent auditor once in a second container with the committed raw and input/oracle read-only; only the audit-output directory writable.
3. No retry, image pull, source edit, or formal rerun. Preserve first outcome. Record exact `docker inspect`, `docker logs`, exit status, raw bytes and audit bytes. Requested resource settings are configuration only unless observed effective enforcement is independently verified.

Formal invocation counts at freeze: candidate 0, auditor 0. The shared OrbStack engine currently has an unrelated running container; do not stop, exec into, inspect its mounts, or modify it. Formal launch awaits an explicit conflict-free lane decision; the already-authorized host construction run is not represented as formal container evidence.
