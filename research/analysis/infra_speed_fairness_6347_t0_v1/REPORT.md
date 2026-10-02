# Issue #6347 — infrastructure-speed fairness T0

## Formal allocation 01 result

Disposition: **PASS_METHOD_SCOPED for the 129 frozen winner/status rows; HOLD for the boundary-gaming claim.** Candidate exit 0 and independent raw-only auditor exit 0, each invoked once in separate OrbStack Docker containers; retries 0. Independent reconstruction matched 129/129 rows and rejected all four frozen output mutations.

In the paired plus held-out delay-swap probes, FRFS changed its winner in 14/14 pairs; the five-tick `batch_rotate` rule changed in 0/14. Arrival FIFO was also insensitive (0/14), but assigned all 12 held-out wins in each arm to principal A. On the 12-opportunity held-out sequence, `batch_rotate` admitted 12/12 opportunities in each arm, split wins 6/6, and had a maximum one consecutive loss per principal. FRFS admitted 12/12, split wins 6/6, and had a maximum two consecutive losses per principal. Arrival FIFO admitted 12/12 but assigned all 12 wins to A, leaving B with 12 losses in a row. These finite counts satisfy the preregistered held-out comparator on this fixture; they do not validate the choice of rotation as a legitimate social right outside the fixture.

Safety controls: critical interrupt and shorter-deadline action bypassed collection; revoked and expired candidates were refused; disjoint resources both proceeded; unresolved decision rights produced HOLD for every policy. The formal auditor reconstructed these rows exactly.

### Boundary evidence limitation and successor

The raw schema retained the winner and admission time but not the collected candidate set. Therefore a winner-only match cannot distinguish “late intent correctly excluded at close” from some incorrect inclusion that happens not to change the winner. Although the frozen comparator models a five-tick close, allocation 01 does **not** establish phase-jitter/boundary robustness or resistance to strategic timing. We retain its outcome unchanged and run a separately preregistered additive boundary-observability successor; no tuning or rerun of allocation 01.

## Execution

- Source base: `f70aa50832ffa84c325237f5367c02332335a156`.
- Image: `python:3.12-slim`, local immutable image ID `sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`, Linux/arm64.
- Engine: OrbStack Docker Engine 29.4.0, Linux/aarch64, cgroup v2. Network disabled; read-only root/source; configured 1 CPU, 256 MiB and 64 PIDs; all capabilities dropped; no-new-privileges. Configured memory is not evidence of host-level hard enforcement.
- Candidate stdout is the retained `candidate.raw.json`; auditor stdout is `audit.raw.json`. Both stderr streams are empty and both exit files contain `0`.
- The initial pre-freeze construction run exposed a missing `arm` tag in boundary/safety rows; that construction failure was corrected before freeze. The preregistered code and hashes below identify the corrected version; the failed construction was not a formal allocation and no formal output was overwritten.

Exact commands, raw output and independent audit are in `results/formal-01/`. Run `python -m unittest -v test_construction` for the four construction tests. `SHA256SUMS` includes the protocol, fixture, source, report and formal output bytes.

## Scope

Synthetic finite scheduler traces only. No real GUI, model/provider, human preference, strategic participant, production clock, lease, effect, product safety, deployment fairness, or human-tempo measurement. A separate boundary successor is required before claiming resistance to timing at the window edge. See [Issue #6347](https://github.com/Unjuno/agent-interface/issues/6347).
