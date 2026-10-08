# Formal T0 report — isolated OrbStack allocation 02

## Outcome

**`PASS_METHOD_SCOPED`** for Issue #6604's deterministic finite-method fixture only. The frozen candidate completed 14 rows in the pinned Python container (exit 0). A separate container ran the independent auditor once (exit 0): all 14 rows replayed, `errors=[]`, the planted slow/fast crossover and no-crossover control were recovered, safety/action/release checks passed, and no semantic claim was made for the unobservable semantic-swap case.

The planted matrix totals were direct=61 and local-periodic=69: pooled scoring selects direct even though local-periodic is better in the slow stratum (10 vs 16), while direct is better in the fast-reversal stratum (45 vs 59). The no-crossover pair retained a consistent local-periodic win (direct=63, local-periodic=31). Other controls totaled direct=47/local-periodic=51. These deterministic, authored fixture totals validate the analysis method; they are not empirical route-effect estimates.

## Formal execution

- Allocation: `DISTURBANCE-TIMESCALE-6604-T0-ISOLATED-ORBSTACK-20261002-02`.
- Base main: `7d7f2f1a1ff281c68c9864ae1c56aa5f68b35ae0`.
- Runtime: dedicated isolated OrbStack Ubuntu 24.04 ARM64 machine with its own Docker Engine 29.1.3 daemon; cgroup v2. Shared daemon and all other task machines/containers were not used or changed.
- Image: `python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`, `linux/arm64`.
- Candidate container `36f72b60ae3488f3bd08dd3330bc0408337f24db097ea7435fb1529ff1edb48d`: started `2026-10-02T08:22:29.396725989Z`, exited `0` at `08:22:29.756783686Z`; log `rows=14 status=COMPLETE`.
- Auditor container `9e953896c4e76a77354669f56b3d7e0e3046fe98eeae85cb4487876ece6837aa`: started `2026-10-02T08:22:38.924595513Z`, exited `0` at `08:22:39.259846388Z`; log `status=PASS_METHOD_SCOPED rows=14 errors=0`.
- Both containers: `network=none`, read-only root filesystem, requested 0.25 CPU / 512 MiB / 64 PIDs. `docker inspect` confirms those configured values and read-only source/raw mounts. The Docker daemon reported VM-visible host capacity of 10 CPUs / 16,819,609,600 bytes despite OrbStack's 1 CPU / 2 GiB machine configuration; effective enforcement of either VM or container limits was not measured and is not claimed.
- Candidate invocation=1; auditor invocation=1; retries=0. Allocation 01 remains an unchanged pre-run shared-engine HOLD.

## Retained evidence

- `candidate.raw.json` SHA-256: `df8d65b7c9f5c32df075c254ad708530bfe27af061bb3269dd1fba6e4ba1c14b`.
- `audit.json` SHA-256: `4b752f6d261ac57edbf57dde2e0598acfefbf207a644bb01742c3718932a3b57`.
- Exact commands, source/image identity, Docker inspect fields, logs, and exit states are retained in `RUN_RECORD.json` and `SUCCESSOR_ISOLATED_ALLOCATION_02.md`.

## Interpretation and limits

This is a successful execution and independent audit of a synthetic method fixture. It supports only the claim that this preregistered analysis distinguishes one planted route-by-stratum crossover from its no-crossover control under the authored numeric schedules. The result is determined by those schedules and the fixed one-tick versus three-tick feedback cadence. There is no GUI, DOOM, model, real actuator, independent natural workload, task-success, route-cost, broad safety, human-tempo, runtime, or product-benefit evidence. No empirical route conclusion follows.
