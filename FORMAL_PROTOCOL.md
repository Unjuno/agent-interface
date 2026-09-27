# Issue #4821 formal protocol

## Lineage and immutable boundary

This is a fresh successor allocation to #4809's terminal one-shot STOP. Preserve #4745, #4800 and #4809 source, freeze, raw results, and audit records unchanged. The new allocation ID is `mitra-gpu-rung0-853-label-encoding-successor-local-20260927-01`.

## Frozen treatment

Use the exact model/config/model-card snapshot and support/query fixture hashes in `FREEZE.json`, with the rev4 dependency closure and pinned Linux/amd64 CUDA image ID. Map the sorted frozen vocabulary `C0`…`C5` to integer IDs 0…5 (`numpy.int64`) before `MitraClassifier.fit`. The returned columns are bound to sorted unique encoded IDs and then explicitly restored to frozen class order before ABI checks or retention. No changes to model, fixture, API, query schedule, dependency set or thresholds.

Before formal launch, validate all frozen hashes and the image ID; verify #4821 remains open, the exact branch and path have no collision, all active GitHub/GitHub-task GPU allocations have terminal or explicitly CPU-only status, the local RTX 3080 is idle, and all running Docker container identities match the freshly recorded allowlist. Freeze that evidence with timestamp immediately before launch. Do not disturb pre-existing containers.

Use one container with `--pull=never --gpus all --network none --read-only`, read-only source/model/fixture mounts, fresh writable output, 1 CPU, 4 GiB RAM and 128 PIDs. Run exactly one direct `MitraClassifier(model_type="Tab2D", device="cuda", fine_tune=False, fine_tune_steps=0, n_estimators=1)` fit/context setup, 16 excluded warmups, 1,024 sequential single-row predictions and 16 repeats of indices 0–15. Instrument model loads and optimizer steps. An independent CPU-only network-disabled read-only container audits complete raw RESULT; typed STOP uses the separate STOP auditor. Preserve invocation receipt, logs, inspect JSON, GPU pre/post snapshots, raw probabilities, per-call wall/CUDA timings, CUDA residency/bytes, process reads and audit logs.

## Decision gates

`PASS_GPU_RUNTIME_ABI_SCOPED` requires exact provenance; one resident CUDA trainer; 1,024/1,024 finite, nonnegative six-class vectors summing to 1 within 1e-4; repeat maximum difference <=1e-6; per-call CUDA event interval and `cuda:0` residency; zero optimizer updates; no formal network; no query process-read delta >=80% checkpoint size; complete raw evidence and independent audit with zero errors; and warm p95 <500 ms. p95 <100 ms additionally qualifies as a `REALTIME_10HZ_CANDIDATE`. A complete valid block at p95 >=500 ms or any checkpoint-scale reread is `REJECT_GPU_HIGH_CADENCE_SHAPE`. Provenance, CUDA, ABI, setup or auditor faults are typed terminal STOP/HOLD/FAIL_INTEGRITY.

One invocation only. Do not retry, tune, replace a row, amend source after launch or reinterpret a STOP as a result. This tests runtime/ABI compatibility only, not task quality, calibration, safety, adaptation, transfer or product benefit.
