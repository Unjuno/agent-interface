# Issue #4828 — extent-aware readout construction

Disposition: **STOP_NUMPY_MISSING_FROM_FROZEN_IMAGE**. This is an environment stop before any model fit, not a scientific result.

## Frozen question

The preregistered construction asks whether adding per-channel global spatial means to the existing global-max readout makes the tiny shared 3x3 CNN construction-competent on the balanced 9x9-positive / 5x5-distractor fixture. It uses one fresh construction dataset seed, one shared initialization, two readout arms, and 1,000 updates per arm. No formal seeds or formal fits are allocated.

## Execution and stop

The six frozen Python source files plus `FREEZE.json` were read back from the allocated GitHub branch and their SHA-256 hashes matched local bytes. The frozen Docker image ID was present locally and matched exactly, but its contents did not match the expected environment: a read-only runtime probe reported Python 3.11.16 and no NumPy module, whereas the freeze specified Python 3.11.2 / NumPy 1.24.2.

The first network-disabled, read-only Docker construction preflight exited 1 at `import numpy` with `ModuleNotFoundError: No module named 'numpy'`. No dataset generation, training, inference, or audit of model outputs occurred. Formal fits: 0; construction fits: 0; retries: 0; image substitutions: 0. The allocation remains terminal; do not retry it or swap images under #4828.

An independent standard-library-only STOP auditor ran in the same image and checks lineage, exact frozen image identity, captured runtime/preflight evidence, resource limits, and zero-fit discipline. It does not run the model or infer a scientific disposition.

## Interpretation and limits

The hypothesis remains untested. Nothing here supports or rejects max-only versus max+mean pooling. A different cached environment, if pursued, requires a separately allocated successor Issue, a fresh freeze and collision/resource check. A local `needle-pilot05:local` container was observed in use by another task during follow-up; it was not entered, stopped, or reused.
