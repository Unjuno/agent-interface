# Issue #6347 — explicit batch-boundary successor

## Result

Allocation `INFRA-SPEED-FAIRNESS-6347-T0-20261002-03` is **PASS_METHOD_SCOPED** for this 16-row synthetic readiness-boundary trace. The candidate and independent raw-only auditor each ran once in separate pinned OrbStack containers, both exit 0, no retries. The auditor exactly reconstructed 16/16 rows and rejected all four frozen mutations.

With A ready at tick 0, a five-tick collection window, equal rights and a predeclared B-first rotation pointer:

| Probe | B ready/submitted | Collected | Deferred | Batch winner |
|---|---:|---|---|---|
| Phase before close | 4 | A, B | — | B |
| Phase after close | 6 | A | B | A |
| Strategic-send proxy before close | 4 | A, B | — | B |
| Strategic-send proxy after close | 6 | A | B | A |

FRFS chose A in these four probes because it was ready first. The 12 repeated windows retained every offered, collected and deferred intent and pointer transition; aggregate batch wins were A=6, B=6. That aggregate balance does not remove the local cutoff discontinuity: moving B from tick 4 to tick 6 changes both collection membership and the winner. Allocation 01's 0/14 delay-swap sensitivity was conditional on its selected delays staying within the five-tick collection window; it must not be generalized across the boundary.

Allocation 02 is preserved separately as `STOP_PRELAUNCH_MAIN_ADVANCED` (candidate=0, auditor=0, containers=0); it was not rerun. Allocation 03 preregistered against the then-current main and ran only after exact source/image/path gates.

## Execution identity

- Source base: `c69fa71501a0e42abc3ffe435ae72949d5d15877`.
- Image: `python:3.12-slim`, local ID `sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`, Linux/arm64.
- OrbStack Docker Engine 29.4.0, Linux/aarch64, cgroup v2; network disabled, read-only root/source, configured 1 CPU/256 MiB/64 PIDs, caps dropped, no-new-privileges. Configured memory is not proof of host hard enforcement.
- Candidate raw: `results/formal-03/candidate.raw.json`; independent audit: `results/formal-03/audit.raw.json`; both stderr files empty, both exit files `0`.
- Construction tests: 4/4 passed before preregistration. Exact argv and stdout/stderr identities are in `results/formal-03/RUN.md`; hashes are in `SHA256SUMS`.

## Limits

This is a deterministic synthetic scheduling counterexample. The delayed-send arm is not a strategic participant study. No actual GUI, synchronized human-origin clock, production arbitration, stakeholder right, human preference, lease, effect, safety, deployment fairness, or useful-latency result is established. Five ticks is a synthetic parameter, not a production recommendation. An actual product policy still needs justified decision rights, deadline and authority revalidation, and real source timing evidence.

See [Issue #6347](https://github.com/Unjuno/agent-interface/issues/6347), allocation 01's distinct [scoped result](../infra_speed_fairness_6347_t0_v1/REPORT.md), and its preserved prelaunch STOP in `results/formal-02/STOP.json`.
