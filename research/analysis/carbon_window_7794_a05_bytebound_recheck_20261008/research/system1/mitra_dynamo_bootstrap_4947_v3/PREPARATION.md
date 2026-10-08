# #5803 import-order construction preparation

**Disposition: PREPARATION ONLY.** This package is not a source freeze or formal result. It contains a minimal early-import helper and candidate runner scaffold for the one declared #5803 intervention: load `torch._dynamo.external_utils` before AutoGluon/Mitra.

## Construction evidence

- Planning base observed on GitHub main: `d3df971ec5e78f557a9798860a4ceefe9c9138fd` (2026-10-01 UTC). The formal freeze must use a fresh exact-main/source/input/model/image readback at a granted start gate.
- The inherited #4821 v2 `runner.py` and `label_abi.py` were compared against current-main GitHub raw contents before the additive copy; their normalized text matched. The only candidate-runner changes are its docstring and delegation of PyTorch/AutoGluon imports to `runtime_imports.load_mitra_runtime()`.
- Python 3.11.9: `python -B -m unittest -v test_runtime_imports` — 2/2 pass. The fake dependency fixture uses Python's real package-import machinery and makes AutoGluon fail unless `torch._dynamo.external_utils` is already loaded. Both tests first failed before their corresponding helper/runner existed, then passed after implementation.
- Inherited audit construction suite: `python -B -m unittest discover -s research/system1/mitra_inference_mode_4821_v2 -p 'test_*.py' -v` — 7/7 pass.
- `py_compile` for the four package Python files passed. No trailing whitespace was found in this package.

## Boundary

No CUDA call, model import/load, Docker/OrbStack command, optimizer step, candidate, or raw auditor was run here. The mock import fixture establishes only the intended ordering contract; it does not reproduce the failure in the pinned image or show that the intervention repairs it. The one-shot GPU/container allocation and exact frozen source/data/image gates in Issue #5803 remain mandatory. Mode drift remains NOT_EVALUATED until that authorized candidate and its separate audit complete.

