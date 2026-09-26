# Construction record — Issue #4482

Date: 2026-09-26 JST. Source intake main: `21dd6a26dbd9f5cb4a6e11b1060902799a76a733`. This is construction-only evidence; no optimizer step or held-out prediction has run.

## Resource and runtime

- Local Windows host; Python 3.11.9; PyTorch 2.5.1+cu121; CUDA 12.1.
- NVIDIA GeForce RTX 3080 Laptop GPU, 16 GiB; construction was a small deterministic batch-16 repeat check.
- `CUBLAS_WORKSPACE_CONFIG=:4096:8` was set before the Python interpreter started.
- No remote workflow, container image pull/build, or package install was used. Existing local CUDA stack was reused.
- Formal allocation is frozen to one invocation and at most 600 optimizer steps; construction is excluded and performs zero optimizer steps.

## Actual CNN shape-path gate

`test_complete_cnn_cpu_shape_path_matches_pool_oracle` ran `TinyGrounder`'s actual pre-pool layers on CPU input `[16,1,100,160]`. The resulting feature map was exactly `[16,16,25,40]`. The `(25,40)->(8,10)` fixed separable matrix pool returned `[16,16,8,10]`, with maximum absolute difference `1.7881393432617188e-07` from CPU `adaptive_avg_pool2d` (gate `<=1e-6`). The same full model returned logits `[16,2]`.

The previous failure expected the reversed spatial order `(40,25)`; no v3 file was changed. V4 binds the corrected dimensions at pool construction and tests the complete CNN path before any formal run.

## Deterministic CUDA control

With deterministic algorithms on, cuDNN deterministic, benchmark off, TF32 off, and the CUBLAS workspace set before interpreter startup, two complete CUDA `TinyGrounder` passes from cloned `[16,1,100,160]` inputs produced bit-identical `[16,2]` logits and bit-identical input gradients. No deterministic-operation exception occurred.

## Construction suites

`test_construction.py`: 5/5 pass, covering manifest and all six exact source-image hashes, pool-vs-oracle, full CPU CNN shape path, strict candidate schema/bounds, and repeated full-CNN deterministic CUDA forward/backward.

`test_audit_controls.py`: 4/4 pass with 18/18 structured corruption variants rejected, including a wrong CNN feature-map declaration. The synthetic clean fixture remains HOLD without safe benefit; aggregate-only gain with a regressed perturbed case remains HOLD; accepted wrong coordinates produce FAIL. These are synthetic auditor controls only, not model training or a formal result.

Combined construction run: 9 tests passed, 18 mutation subtests passed. Formal invocations before freeze/run: 0. No scientific outcome, runtime promotion, or generalization claim is made here.
