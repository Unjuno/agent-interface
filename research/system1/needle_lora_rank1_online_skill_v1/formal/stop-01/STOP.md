# Formal allocation 01 — STOP before training

Allocation: `needle-lora-rank1-online-skill-v1` (Issue #4507).

The single formal host orchestration invoked one isolated training container and stopped with exit code 1 before model/data evaluation or any optimizer step. The frozen runner requires an empty output mount, while the frozen host wrapper had already written `FORMAL_INVOCATION.json` there. The exact container stderr is retained in `training.stderr.txt`; it ends with `dedicated_empty_output_directory_required`.

Disposition: `STOP_OUTPUT_DIRECTORY_CONTRACT_MISMATCH`. The audit container did not start. Formal orchestrations: 1; training-container invocations: 1; optimizer updates: 0; model evaluations: 0; retry: 0. This is not a scientific quality result. Do not rerun this allocation or alter its frozen source. A prospective allocation may keep the Issue's scientific question but must have a distinct identity/source/output path and fix the mount layout before formal execution.
