# Issue #7944 T0 A01 — bandwidth inheritance finite-method test

This additive offline research package tests the budget-attribution hypothesis in [Issue #7944](https://github.com/Unjuno/agent-interface/issues/7944). It preserves the issue's scope: no runtime scheduler, OS setting, GUI, model, user, or physical-input claim.

## Frozen question

In a finite integer-tick uniprocessor model, does BWI-style charging reduce freshness-deadline misses against priority inheritance charged to an exhausted holder's home reservation, while conserving service and failing closed on invalid wait edges? Three policy arms use the same frozen `(Q,P)` servers, workloads, total admitted bandwidth, EDF/tie rules, and horizon.

## Protocol and outputs

- `PROTOCOL.md`, `fixture.json`, `FREEZE.json`: H/T/D/C/U, exact finite contract, cases, and source identities.
- `candidate.py`: one-shot deterministic policy simulator.
- `audit.py`: separately implemented raw-only schedule reconstruction and mutation rejection.
- `test_construction.py`: pre-freeze discriminator, boundary, nested-chain, cancellation, invalid-edge, budget-conservation and mutation checks.
- `ENVIRONMENT.json`: host/runtime provenance and explicit OrbStack image-store stop.
- `results/candidate.raw.json`, `results/AUDIT.json`: one formal candidate output and one audit output.
- `REPORT.md`, `SHA256SUMS`: disposition and integrity evidence.

## Environment

OrbStack's Docker API responds, but `docker images` and a no-network `python:3.12-slim` run both fail on unreadable containerd content blobs (`operation not supported`). No image or daemon repair was attempted. This standard-library finite model has no container-specific requirement, so the protocol freezes host-only CPython 3.14.5; it makes no isolation/resource-enforcement claim.

## Reproduction boundary

Before the formal freeze, run:

```sh
python3 -B -m unittest discover -s research/analysis/bandwidth_inheritance_7944_t0_a01_20261005 -p 'test_construction.py' -v
```

Verify all entries in `FREEZE.json`, then run the candidate exactly once and the auditor exactly once using the commands retained in `REPORT.md`. Do not repeat either formal invocation. A code correction after freeze belongs in a distinct successor allocation; preserve this raw result and audit unchanged.

## Claim ceiling

The model uses fixed absolute server deadlines and replenishes an exhausted server by `Q` at that deadline. It is CBS-like, not a full CBS implementation or a general schedulability result. Even a scoped pass only establishes the declared finite method behavior; it does not prove Agent Interface has a corresponding schedulable CPU-backed resource or that BWI improves live verifier latency.
