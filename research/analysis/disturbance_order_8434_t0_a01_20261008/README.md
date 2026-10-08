# Issue #8434 — disturbance-order correlation T0 A01

Status: **frozen; formal candidate/auditor run pending preregistration**.

This additive successor holds disturbance counts (16 A, 16 B), per-event intensity, duration, and 32-opportunity horizon fixed while contrasting IID, clustered, alternating, and held-out block orderings. Two fixed stateful synthetic route laws are compared alongside an order-invariant null pair. The question is whether schedule structure changes the route ranking on disjoint held-out seeds, not whether real GUI or game workloads have these properties.

## Frozen package

- `SOURCE.json` — workload, schedule rules, split seeds, and decision gate.
- `PROTOCOL.md` — H/T/D/C/U, execution boundary, and reproduction commands.
- `candidate.py` — schedule and per-opportunity raw-output generator.
- `audit.py` — separate raw-only schedule and outcome reconstruction; imports no candidate code.
- `test_contract.py` — test-first behavior and hostile mutation controls.
- `FREEZE.json` — base-main identity, source hashes, execution boundary, and one-shot invocation limits.

The initial RED was the expected missing-candidate import. The implementation then passed the construction suite in normal and optimized Python. Formal execution is host-only because the OrbStack Docker daemon's image listing failed on its known containerd content-store `operation not supported` condition; no container was started and no isolation is claimed.

`formal_01/` will contain the one-shot raw, independent audit, and run receipt after preregistration. A formal STOP or failure will remain intact; no retry or relabeling is allowed.
