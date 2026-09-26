# Issue #4471 — formal report

## Disposition

`STOP_FORMAL_RESULT_SERIALIZATION_NAMEERROR_AFTER_TRAINING`. The one local-host GPU run was not scientifically classifiable: output construction failed after the training and scoring steps, leaving no retained predictions or metrics.

## What happened

- Frozen source: `runner.py`, SHA-256 `b9dcf1e9720adef96e095d02e26bd61171c5453ba382880300cca11efaadd357`, Git blob `e76e1582f12db745c5c3b1140b1393079265fff7`.
- Exactly one invocation, exit code 1, 2026-09-26 14:08:08–14:08:13 UTC.
- The fixed 400-step base fit, four 120-step adapter fits, and six 4,096-row scoring calls occur before result-dictionary construction. There, `steps_per_update` referenced undefined `STEPS` after the step variable had been split into `BASE_STEPS` and `ADAPTER_STEPS`.
- By control flow, 880 optimizer-step calls were completed and predictions for the routed and shared A/B/C arms were computed in memory. This is inferred from reaching the failure line; no per-step receipts were emitted.
- Stdout is empty (0 bytes). No JSON result, metric rows, model state, snapshot, or audit input was persisted. Do not infer accuracy from this run.
- Captured stderr is 723 bytes with SHA-256 `26dde93146e5d032aa9339daf04964d2e1a391190ee4a8fdd6459f8935d3f87e`; exact bytes are stored in `FORMAL_STDERR.raw.b64`.

## Decision and preservation

This is a formal artifact/protocol STOP, not a model-quality FAIL or HOLD. No retry, altered-source rerun, tuning, or attempt to reconstruct outputs was made. #3895's earlier seed-3444 result and its `HOLD_PROTOCOL_DEVIATION` remain intact. A future attempt requires a distinct successor Issue, new seed/allocation, corrected output-schema tests, and fresh exact source freeze.

Local host only: Windows RTX 3080 Laptop GPU, Python 3.11.9, PyTorch 2.5.1+cu121, CUDA 12.1, deterministic CUDA with `CUBLAS_WORKSPACE_CONFIG=:4096:8`, TF32 disabled. No container claim. Peak allocated GPU memory is typed `UNAVAILABLE_WDDM`.
