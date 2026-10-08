# Issue #4947 frozen diagnostic protocol

## Inputs and environment

Use the exact #4821 model/config/card, support/query bytes, label ABI and rev4 dependency closure. The mounted model root is `/model`; `hf_model` must receive that directory, never `/model/model.safetensors`. Prelaunch tests assert this exact source contract. Pin CUDA image `sha256:01ea4e60b03e8a7d48644d0dce596bd2e42ab3815fdc52b0c7a6d4cbcf757dac` (linux/amd64; PyTorch 2.5.1+cu121, CUDA 12.1). No download, package install, network, or image pull.

Run once in a fresh output directory with source/input/model mounted read-only; `--pull=never --gpus all --network none --read-only --cpus=1 --memory=4g --pids-limit=128`. Do not stop or change existing containers. Recheck main, issue/branch/path, active allocations and Docker/GPU state immediately before launch. If a competing GPU or timing-sensitive CPU Docker allocation is active, or any hash/device/image gate fails, write only a typed pre-run STOP.

## Runner

`probe.py` imports the exact #4821 runner, loads byte-pinned inputs, fits one support context with `fine_tune=False`, `fine_tune_steps=0`, `n_estimators=1`, `device="cuda"`, and `hf_model=str(base.MODEL)`. It verifies one model load and zero optimizer steps. After capturing every resident module's natural training flag, it compares 16 query rows × four distinct Python/NumPy/CPU-Torch/CUDA-Torch RNG states × two modes. Arm A restores exact natural flags; arm B calls `eval()` immediately before `predict_proba`. Arm order is counterbalanced by row; matched calls start from the same RNG state. The model, weights, fixtures and output class-column mapping remain identical.

Retain 128 probability vectors, module state before/after each call, CUDA-event receipts, runtime/input/model/freeze hashes, model load and optimizer counters, and complete invocation/log receipts. No task labels or threshold decisions are computed.

## Audit and decision

Run the standard-library-only `audit.py` in a second network-disabled read-only container with RAW mounted read-only and only audit output writable. It validates freeze/source/input/model/image identity, the exact unique 128-row matrix, finite nonnegative six-class vectors summing to one, counterbalanced order, natural-mode restoration, eval-arm module/dropout state, and zero optimizer steps. Construction tests reject duplicate rows, NaN probabilities, active dropout in arm B, source tampering and freeze hash tampering; a static test locks the model directory argument.

`PASS_EVAL_MODE_EXPLAINS_REPEAT_DRIFT_SCOPED` only if audit errors are empty, natural mode has an active dropout module, at least 8/16 A rows have same-row maximum probability range >1e-6, all 16 B rows have range <=1e-6, and median B range is at most one tenth of median A range. Otherwise a valid complete diagnostic is `REJECT_EVAL_MODE_CAUSE_SCOPED`. Any source, asset, resource, CUDA or audit defect is STOP/HOLD. One GPU invocation, zero retries.

