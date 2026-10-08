# S04 construction record

Allocation: `ERROR-CARRY-6081-S04-WSLC-20261003-01`.

- Host Python 3.11: `python -m unittest -v test_s04` — 9 tests passed.
- Host syntax check: `python -m py_compile candidate.py build_cases.py audit.py` — exit 0.
- Regenerated request matrix to a temporary file and compared SHA-256 with frozen `cases.json` — identical.
- WSLc 3.0.1.0, Linux kernel 6.18.40.1-1; cached image `python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`, local image ID `sha256:9e87977b867847e186d066f531ef783b006d582a985c341c269446088d90f2c4`, Python 3.12.14, amd64.
- Before the disposable run, `wslc list` showed no running containers. The construction suite was run in a separate `--rm`, `--pull=never`, `--network=none`, `--cpus=1`, `--memory=512M`, non-root container, with the study directory mounted read-only. Result: 9/9 passed, exit 0.
- WSLc emitted: `Your kernel does not support swap limit capabilities or the cgroup is not mounted. Memory limited without swap.` Therefore memory was requested, but swap exclusion/resource enforcement was not fully verified; do not claim it was.
- The test import created a local `__pycache__`; formal read-only mounts exclude writes to the source package and set `PYTHONDONTWRITEBYTECODE=1`.
- One earlier host invocation from the repository root used the test module name without the package working directory and failed with `ModuleNotFoundError`; it did not run candidate code. The corrected working-directory invocation passed. An earlier test-first import failure was expected during TDD and is not a construction pass.

This is a synthetic exact-arithmetic method study only. No GPU is relevant to this small deterministic workload; no live input, physical actuator, GUI, or game was touched.
