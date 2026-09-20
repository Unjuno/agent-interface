# GPU photometric augmentation comparison — preregistration

Issue #3682, successor to #2912. First source images are public retained Chromium fixture artifacts; prior CPU/nearest-neighbor outcomes are unchanged.

Execution amendment before model allocation: the CUDA container image pull was stopped before training when it reduced local C: free space to 784,015,360 bytes. The recorded stop is retained in `CONTAINER_PREFLIGHT_STOP.md` and the GitHub issue. Use the already-installed PC-local Windows CUDA/PyTorch environment for the single formal model process; the scientific design below is unchanged. Do not build/pull another CUDA image in this allocation.

## H/T/D/C/U

**H.** A small CNN trained with training-only multiplicative brightness augmentation will improve grounding on held-out source screenshots under the already-observed dark/bright nuisances versus the same model without augmentation.

**T.** Freeze base commit `d9776a90662e1d7f901a025395aa27e28d9d4d00`, image-label manifest SHA-256 `5af3901c0d579bf1e65ff9d36931fa033f116de5f66a156670d8d650851497b0`, and all six image hashes in `SOURCE_MANIFEST.json`. Train only on tasks 1, 2, 4, 5; hold out complete task-3 (A) and task-6 (B) screenshots. Evaluate each held-out source at original brightness and deterministic 0.85x/1.15x pixel intensity, round-half-up and clamp [0,255].

**D.** One PC-local Windows Python process using the preinstalled PyTorch CUDA runtime; no new CUDA container build/pull and no network calls. Two arms in fixed order: no brightness augmentation, then brightness augmentation. Both use the same 4 source rows, class-balanced sample-index schedule, model, initialization seed 2912, Adam settings, and 300 optimizer steps. Augmented arm samples one independent uniform intensity factor `[0.70, 1.30]` per training sample per step. Eval uses the 6 frozen cases only. Record per-case logits/probabilities, route at top-class confidence >=0.75 (accept), [0.25,0.75) (YIELD), <0.25 (reject), mapped coordinates, strict validator output, exactness, wall time, and peak GPU allocation. No tuning from evaluation.

**Model.** Grayscale 160x100 input; `Conv(1,8,3,pad=1)-ReLU-MaxPool2`, `Conv(8,16,3,pad=1)-ReLU-MaxPool2`, adaptive pool 8x10, `Linear(1280,32)-ReLU-Linear(32,2)`. Cross-entropy; Adam lr=0.001; batch size 16 sampled with replacement from the four training images; 300 fixed optimizer steps. Each arm starts from the same CPU-created initialization state. CUDA deterministic algorithms enabled; `CUBLAS_WORKSPACE_CONFIG=:4096:8`, cuDNN deterministic true, benchmark false, TF32 disabled. Runtime: host Python 3.11 / PyTorch 2.5.1+cu121 / CUDA 12.1 / RTX 3080 Laptop 16 GiB / driver 581.57; Pillow 10.4.0. RGB-to-gray and bilinear resize to 160x100 are pinned by Pillow. All seeds and exact implementation bytes are frozen by this commit before execution.

**C.** No GUI, button-down, task submission, provider/host IPC, authority grant, or runtime promotion. The classifier selects only layout A/B; field/submit coordinates come from training rows only and then pass `compiled_form_grounding_v1.validate`. The validator proves schema/bounds only; exact coordinates are scored separately. No source-image augmentation crosses the whole-image holdout.

**U.** Two held-out images (one per known layout); transformed variants are not independent examples. A result cannot establish unseen-layout transfer, calibration, operational utility, or general GUI robustness. GPU feasibility does not imply GPU necessity for deployment.

## Frozen cases and source identity

| Task | Layout | Role | Source sequence | SHA-256 |
|---|---|---|---:|---|
| task-1 | A | train | 8 | `3fd0c515a1f0358fb4afa328f60d2a1b82a748018ff4295fad5ec3922f3640ec` |
| task-2 | A | train | 30 | `8ce9f5bdb642592122e0f7ed2c84656729564ced3d25c14af6b787c71ef8ce7a` |
| task-3 | A | held-out | 53 | `3e81cc92439d01aeabd69c8cfd9f2a2eb842b3433f41771fe3b0409e331f9349` |
| task-4 | B | train | 76 | `ae2974269932d767fbfba536287c2f8c02c1ffb77efaed6c3c87b20c250fbad4` |
| task-5 | B | train | 99 | `7216758322e41ff158751f70623401089df7080011fdac5c9ea59ea7b49b559a` |
| task-6 | B | held-out | 122 | `ccc8662251de86ee477e8ff149ce19c67de8e26bb93f5ead264fe268438118bd` |

Note: task-3 hash must be checked against the canonical manifest and actual bytes before execution; any mismatch is a pre-allocation STOP.

## Disposition

`PASS_PHOTOMETRIC_AUGMENTATION_SCOPED` only if source/audit integrity passes, all schema candidates validate, neither arm accepts an incorrect coordinate, and the augmented arm is no worse on the four perturbed cases with a strict exactness improvement on at least one. Otherwise retain `HOLD_NO_SAFE_BENEFIT`; any accepted incorrect coordinate is `FAIL_ACCEPTED_FALSE_GROUNDING`. Missing source, nondeterminism, host GPU/runtime loss, or a training error is a STOP, with no retry.
