# Issue #5518 T7 — input-conditioned bounded quiescence deadline

## H/T/D/C/U

- **H:** A finite adapter conformance checker can distinguish permitted quiescence while an observation is pending from silence after its declared logical deadline. At the inclusive 2-tick boundary, `QUIESCENT` remains permitted; one tick later it is forbidden and an explicit `UNKNOWN` remains a valid output. Hidden internal retry/batching does not change the visible conformance verdict. After `CANCELLED`, quiescence is not permitted because no observation is pending.
- **T:** One deterministic six-trace finite-state contract in a pinned, network-disabled, CPU/memory-limited OrbStack Python 3.12 container. Inputs are `OBSERVE@0` or `CANCEL@0`; logical time is integer ticks; output labels are `RECEIPT`, `QUIESCENT`, `UNKNOWN`, and `CANCELLED`; a hidden `TAU_RETRY` event is excluded from the visible I/O trace. The pending-observation deadline is exactly tick 2. A separately authored auditor reconstructs first-forbidden-event prefixes. No wall-clock timing, model, GUI, network, external service, or tuning.
- **D:** PASS iff: (1) `RECEIPT@1`, `QUIESCENT@2`, and explicit `UNKNOWN@3` after OBSERVE conform; (2) `QUIESCENT@3` and `RECEIPT@3` are rejected at the first output; (3) `QUIESCENT@1` after `CANCELLED` is rejected at that first forbidden event; (4) an internal retry leaves the external verdict unchanged; and (5) an independent replay agrees on all six traces. Any conforming trace rejected, forbidden output accepted, or oracle mismatch is FAIL.
- **C:** The exact `2` tick bound is an authored contract constant, not an empirically justified real timeout. Real adapters may need a different source-grounded bound or no quiescence claim; this experiment tests enforcement of a declared bound only.
- **U:** Integer logical ticks are not milliseconds or scheduler time. No real transport, timing distribution, fairness, GUI behavior, production ABI, task success, or human-tempo claim.

## Frozen six-trace matrix

| Case | Input / output history | Expected |
|---|---|---|
| `receipt_before_deadline` | OBSERVE@0, hidden TAU_RETRY@0, RECEIPT@1 | conform |
| `quiescent_at_deadline` | OBSERVE@0, QUIESCENT@2 | conform (inclusive bound) |
| `quiescent_after_deadline` | OBSERVE@0, QUIESCENT@3 | reject at output index 1 |
| `explicit_unknown_after_deadline` | OBSERVE@0, UNKNOWN@3 | conform (explicit uncertainty) |
| `late_receipt` | OBSERVE@0, RECEIPT@3 | reject at output index 1 |
| `cancel_then_quiescent` | CANCEL@0, CANCELLED@0, QUIESCENT@1 | reject at output index 2 |

This is a new phase/boundary discriminator; T0–T6b remain unchanged. No reruns or retries of this allocation. An infrastructure failure is retained as STOP; any changed tick bound or matrix requires separate preregistration.

## Execution freeze

Base HEAD: `ddd2a4b473f7418665619cdacff60cc2b306ad95`. OrbStack Docker Linux/ARM64, `--network none`, `--cpus=1`, `--memory=512m`. Image: `python:3.12-slim@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`. Runner/auditor/control hashes are posted on Issue #5518 before the single formal run.

- Runner SHA-256: `1feef108a7c81adafa1bb00d55d093c7e9244a42b8a7a445cb2dc7b7f0e700b8`
- Independent auditor SHA-256: `f399ff846f9756601d0e3ea52e0b138486e1bc425d02236f91d4a0f1cd2f88b3`
- Mutation controls SHA-256: `490a444e77c9ca0e132a92052bbf9cba5f5695afe8c2732bab3a2b4426ceeab8`

Exact single allocation command:

```sh
docker run --rm --network none --cpus=1 --memory=512m \
  -v "$PWD/research/analysis/ioco_5518_t7_tick_bound:/work" \
  python:3.12-slim@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f \
  python /work/experiment.py --outdir /work/raw/formal
```

## Lineage

Issue #5518 T0–T6b already tested input-conditioned output sets, explicit UNKNOWN, forbidden outputs, shortest counterexamples, nondeterministic output sets, bounded quiescence after RECEIPT, and a 28-history quiescence audit. T7 isolates a new integer-deadline boundary while an observation is pending, explicit UNKNOWN after that deadline, hidden internal retry projection, and post-CANCEL quiescence.
