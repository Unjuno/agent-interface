# Online LoRA skill stream: resume experiment

Issue: [#3911](https://github.com/Unjuno/agent-interface/issues/3911). Predecessors: #3769 and #3890. Formal evidence is under `formal/`; preregistered gates and source hashes are in `FREEZE.json`.

## Disposition: FAIL (pre-registered gates)

The adapter tensors, AdamW moments/steps, feedback cursor, and immutable base matched the uninterrupted in-memory reference at all 16 arrivals for all three seeds. All 16 arrivals per seed ran in distinct fresh worker PIDs. The hash chain and fail-closed malformed/stale/duplicate/skipped controls passed. The independent auditor independently regenerated training and found no adapter/optimizer divergence.

Two pre-registered gates did not pass:

| Seed | B heldout accuracy (diagnostic) | Max milestone logit delta | Predictions equal | Update-only p95 | Gate |
|---|---:|---:|---|---:|---|
| 39111 | 0.8613 | 1.91e-6 | yes | 209.22 ms | FAIL |
| 39112 | 0.9429 | 3.82e-6 | yes | 101.57 ms | FAIL |
| 39113 | 0.9314 | 1.91e-6 | yes | 68.32 ms | FAIL |

The preregistration required bit-exact heldout logits, not merely matching predictions; small CPU floating-point differences therefore fail that gate. It also required update-only p95 <=60 ms; every seed exceeded it. Fresh-process wall p95 (including interpreter startup and serialization) was 4025.73, 4101.62, and 2113.13 ms, respectively, and is not the update-only gate.

The first auditor invocation stopped on an auditor-only lookup error: it expected `fresh_process_wall_ms` in each worker JSON, while the runner stores those values in `orchestration.json`. The auditor was corrected without changing runner, checkpoint, reference, data, or thresholds; this correction is disclosed in `AUDIT_SOURCE_CORRECTION.md`. The successful audit run then detected the two gate failures above. No training rerun, tuning, seed replacement, or threshold relaxation was performed.

## Scope

Evidence supports exact resumability of this synthetic rank-2 LoRA/AdamW state at the serialized tensor/state level under this fixed local CPU setup. It does not establish bit-exact inference logits across fresh processes, the 60 ms update budget, real-user feedback quality, general skill transfer, authenticity against a hostile writer, concurrent inference/training safety, or production readiness. The image emitted a benign warning that NumPy is unavailable; the experiment uses only PyTorch and JSON and completed.

Formal run used cached image ID `sha256:6ab7a93188dd60d3832a0be8b5266418e0de1253159c5c66e64562a85fd4a10e`, Linux/amd64, one CPU, 2 GiB memory, network disabled. Builder/reference and auditor used separate containers. Raw per-arrival packages, worker metadata, schedules, heldout logits/predictions, and orchestration records are retained in `formal/seed-*`.
