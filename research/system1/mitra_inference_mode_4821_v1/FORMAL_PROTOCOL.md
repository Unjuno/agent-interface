# Issue #4935 frozen diagnostic protocol

## Inputs and environment

Use only the current-main #4821 package source and assets matching the stored SHA-256 values: the 302,717,904-byte `model.safetensors`, support CSV, query CSV, config/card, and wheel manifest. Pin CUDA image `sha256:01ea4e60b03e8a7d48644d0dce596bd2e42ab3815fdc52b0c7a6d4cbcf757dac` (linux/amd64, PyTorch 2.5.1+cu121, CUDA 12.1). No download, package installation, network, or image pull.

Run once in a new output directory with source/input/model mounted read-only; `--pull=never --gpus all --network none --read-only --cpus=1 --memory=4g --pids-limit=128`. Never stop or change existing containers. Recheck the issue/branch/path, active local task allocations and Docker/GPU state immediately before launch. If any competing timing-sensitive allocation is running or the RTX 3080 identity/image/input gate fails, write only a typed pre-run STOP and do not run the probe.

## Runner

`probe.py` imports the hash-pinned #4821 runner and executes its exact support context setup once with `fine_tune=False`, `fine_tune_steps=0`, and `n_estimators=1`. Verify zero optimizer steps. Capture every module's natural training flag after fit. For each of query rows 0–15, pre-generate four distinct Python/NumPy/CPU-Torch/CUDA-Torch RNG states. Run arms A and B in counterbalanced row order; for each repetition restore the same RNG state before its matched A/B calls. A restores exact natural module flags; B calls `eval()` before the call. Capture every module's flags before and after each call. Keep the identical model, weights, fixtures and class-column ABI throughout.

The runner retains 128 probability vectors (16 rows × 4 repetitions × 2 arms), module states, CUDA event timing receipts, runtime/input/model hashes, context setup duration, model load calls, and optimizer-step count. It does not compute task labels or threshold decisions.

## Audit and decision

Run the separate standard-library-only `audit.py` in a second network-disabled read-only container, with RAW mounted read-only and only audit output writable. It validates the full unique 128-row matrix, finite nonnegative six-class probability vectors summing to one, mode evidence, eval-arm dropout state, and zero optimizer steps. Synthetic unit controls must reject duplicate rows, NaN probabilities, and active dropout in arm B.

`PASS_EVAL_MODE_EXPLAINS_REPEAT_DRIFT_SCOPED` only if audit errors are empty, natural mode has at least one active dropout module, at least 8/16 A rows have same-row maximum probability range >1e-6, all 16 B rows have range <=1e-6, and median B range is at most one tenth of median A range. Otherwise a complete valid diagnostic is `REJECT_EVAL_MODE_CAUSE_SCOPED`. Any source, asset, resource, CUDA or audit defect is STOP/HOLD. One GPU invocation, zero retries.
