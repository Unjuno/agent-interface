# Issue #4809 formal run amendment

This successor retains the exact #4745 model revision, support/query CSVs, environment floor, single-resident-estimator method and frozen decision thresholds. Its only runtime-environment addition is the hash-pinned #4800 rev4 dependency closure on the same pinned PyTorch/CUDA base image.

## Preformal correction

Before any model invocation, review found that the inherited #4745 runner's exception handler hard-codes allocation `mitra-gpu-rung0-853-successor-local-20260927-01`, and its result/STOP schemas identify #4745. This would misattribute any STOP produced by this successor. The #4809 runner now serializes its own allocation and #4809 result/STOP schema. The scientific procedure, model call, data, gates, metrics and thresholds are unchanged. The independent audit and four synthetic audit controls were updated for the successor result schema. The corrected source hashes are frozen in `FREEZE.json`.

## Runtime

Build `Dockerfile.rev4` from the exact cached CUDA base with networking disabled and no GPU. The build installs the original 59-distribution #4745 lock and the five hash-pinned #4800 rev4 distributions from the 64-file wheelhouse. The final image ID is pinned in `FREEZE.json`.

The single formal container gets one `--gpus all` request, network disabled, immutable `/src`, `/inputs`, and `/model` mounts, a fresh writable `/out` mount, 1 CPU, 4 GiB RAM, 128 PIDs, and a 512 MiB tmpfs. Only the exact predeclared runner entrypoint may load the checkpoint and call `fit`/`predict_proba`. It runs 16 warmups, 1,024 sequential single-row queries, and 16 repeats. Do not retry or change anything after model invocation.

An independent CPU-only, network-disabled, read-only helper then runs `audit.py` against a complete result. For a typed STOP, a separate stop-record auditor validates the result metadata and retains the entire process log and terminal container state. Neither audit imports torch or requests a GPU.
