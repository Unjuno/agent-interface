# Issue #4621 — online Needle LoRA snapshot-cadence result

**Disposition: `HOLD_NO_PERSISTENCE_BENEFIT`.** Integrity and exact-resume gates passed, and lower checkpoint cadence reduced amortized persistence overhead. No cadence met the preregistered 60 ms total per-feedback p95 limit, so none qualifies as a scoped candidate.

## Execution and audit

- One frozen local Docker orchestration; training and independent auditor containers each ran once and exited 0. Retry/tuning/seed replacement: 0.
- Cached image `needle-pilot05:local`, ID `sha256:6ab7a93188dd60d3832a0be8b5266418e0de1253159c5c66e64562a85fd4a10e`; Docker 29.8.0, linux/amd64, Python 3.12.14, PyTorch 2.5.1+cpu, one thread, network disabled, source/root read-only, 1 CPU / 2 GiB / 64 PIDs.
- Seeds 77111, 77222, 77333; 16 feedback arrivals per seed; uninterrupted reference plus cadence 1/4/16; 63 durable checkpoint snapshots and 72 fresh worker processes including final restore validators.
- Independent raw-only audit recomputed the held-out predictions from recorded base/adapter states, labels, inputs, schedule, and checked source, checkpoint and output digests. **0 audit errors.** All 144 resumed per-arrival adapter/optimizer/prediction states exactly matched the uninterrupted reference. Base states remained unchanged. All 9 corrupted/stale/duplicate/skipped/schema/role/base/schedule controls were rejected; route controls passed.
- Raw training output contains 151 ZIP entries (including directory entries); lossless ZIP round-trip SHA-256 comparison checked every entry with 0 mismatches. `RAW_TRAINING.zip` SHA-256: `6405c1f72aadcdfed45c411470c7ee3f542e94b2f6d464b173fe969e5c08ef6f` (2,845,319 bytes).

## Matched held-out skill quality (descriptive, not the persistence gate)

| Seed | Frozen role A accuracy | Final role B accuracy |
|---:|---:|---:|
| 77111 | 95.68% | 90.63% |
| 77222 | 96.83% | 92.21% |
| 77333 | 97.51% | 87.96% |

The final B score on seed 77333 was below 0.90; this experiment tests resume equivalence, not a new skill-quality pass. It does not support a general task-utility claim.

## Latency and durability trade-off

Aggregate p95 columns below are the mean of the three per-seed p95 statistics, as emitted by the frozen auditor. All times are milliseconds.

| Checkpoint cadence K | Update-only p95 | Boundary checkpoint+resume p95 | Persistence overhead / feedback (mean) | Total / feedback p95 | Maximum unsaved feedback on crash |
|---:|---:|---:|---:|---:|---:|
| 1 | 8.88 | 2449.31 | 1803.09 | 2454.36 | 0 |
| 4 | 6.82 | 1869.61 | 444.45 | 473.12 | 3 |
| 16 | 4.91 | 1713.69 | 107.11 | 112.02 | 15 |

Cadence 4 and 16 reduced mean persistence overhead per feedback by 75.35% and 94.06% relative to cadence 1. However, cadence 16 still missed the 60 ms total-p95 gate in all three seeds (104.32, 107.36, 124.38 ms); cadences 1 and 4 also missed in every seed. The update-only step itself was below 14 ms in all seed/cadence cells; fresh-process startup/state restoration dominates this local measurement. Cadence 16 also permits up to 15 feedback updates to be unsaved at a crash.

## Scope

This establishes exact resume and a local CPU snapshot-overhead trade-off only for this synthetic 8→16→4 network, pinned container and host. It does not measure real Astra feedback, GUI/task effects, concurrent inference/training, cross-hardware behavior, real-time application control, or action authority. It is not a runtime promotion. V1's separate pre-training host-wrapper STOP remains preserved under `provenance/PREDECESSOR_STOP.json`; v1 was never retried.
