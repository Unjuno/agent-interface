# A02 construction and preflight tests

Before the sole GPU candidate, the immutable source package was checked locally:

- `py -3.11 -B -m unittest -v test_capture`: **6/6 pass**. Tests cover complete durable publication, truncated JSON retention without scientific publication, setup STOP, frozen-source mismatch, completed parity-failure retention for audit, and refusal to overwrite an existing raw. The no-overwrite test was first run RED against the initial implementation, then passed after the fail-closed guard was added.
- `pwsh -NoLogo -NoProfile -File .\gate_correction\test_gpu_preflight_gate.ps1`: **8/8 pass** for null/empty/whitespace inventory, active app, nonzero/unparseable GPU state, and command failures.
- `py -3.11 -B -m py_compile benchmark.py audit.py run_capture.py test_capture.py`: exit 0.

These are construction checks, not CUDA evidence. The candidate and the raw-only auditor are separately retained in `raw/`.
