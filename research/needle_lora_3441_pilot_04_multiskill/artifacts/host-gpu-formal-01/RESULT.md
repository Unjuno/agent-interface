# Pilot-04 formal allocation result

**Outcome: STOP_FORMAL_CUBLAS_DETERMINISM_CONFIGURATION.** This is not an accuracy FAIL or PASS.

The frozen Windows-host GPU allocation was invoked once. PyTorch reached the first base-pretraining backward pass and stopped because deterministic CUDA execution requires `CUBLAS_WORKSPACE_CONFIG=:4096:8` or `:16:8` to be set before process startup. The failure happened before the first optimizer update: zero optimizer steps, held-out queries, scores, adapter updates, or snapshot checks.

The exact diagnostic and command are retained in [runner_exception.txt](runner_exception.txt). No retry or source change was made to this allocation. A future attempt needs a distinct successor allocation with the workspace environment included in the freeze.

Construction-only checks remain 5/5 PASS; they are not formal model evidence. Docker is separately STOP because Docker Desktop's Linux engine pipe is absent/service stopped. Per #3701, this attempt used the explicitly allowed Windows RTX 3080 host fallback and is not a container result. No workflow was used.

Scope remains synthetic only; no runtime, GUI, vision, action-authority, or generalization claim.