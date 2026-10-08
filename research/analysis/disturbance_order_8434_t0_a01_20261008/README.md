# Issue #8434 — disturbance-order correlation T0 A01

Status: **PASS_METHOD_SCOPED** for the frozen finite authored method fixture. This is not an empirical interface, game, or workload result.

This additive successor holds disturbance counts (16 A, 16 B), per-event intensity, duration, and 32-opportunity horizon fixed while contrasting IID, clustered, alternating, and held-out block orderings. Two fixed stateful synthetic route laws are compared alongside an order-invariant null pair. The question is whether schedule structure changes the route ranking on disjoint held-out seeds, not whether real GUI or game workloads have these properties.

## Frozen package

- `SOURCE.json` — workload, schedule rules, split seeds, and decision gate.
- `PROTOCOL.md` — H/T/D/C/U, execution boundary, and reproduction commands.
- `candidate.py` — schedule and per-opportunity raw-output generator.
- `audit.py` — separate raw-only schedule and outcome reconstruction; imports no candidate code.
- `test_contract.py` — test-first behavior and hostile mutation controls.
- `FREEZE.json` — base-main identity, source hashes, execution boundary, and one-shot invocation limits.
- `formal_01/RUN.json`, `RAW.json`, and `AUDIT.json` — the immutable one-shot execution receipt and outputs.

The initial RED was the expected missing-candidate import. The implementation passed the construction suite in normal and optimized Python. Formal execution then ran once on host Python 3.14.5, offline and without a container: the candidate and independent auditor each exited 0, with zero retries, and the auditor accepted all 96 cases. The OrbStack image-list preflight had failed with the recorded containerd content-store `operation not supported` condition; no container was started and no isolation is claimed. Exact hashes and the scoped result are in `formal_01/RUN.json` and `REPORT.md`.

A formal STOP or failure remains preserved; no retry or relabeling is allowed. The result is limited to the authored simulator and its declared route laws. It does not establish real disturbance correlations, GUI/game behavior, route efficacy, safety, human tempo, or a product recommendation; any T1/live transfer requires a separate authorized allocation.
