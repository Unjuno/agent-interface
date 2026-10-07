# Supplemental bundled-runtime validation

The initial local Python 3.12.13 interpreter lacked Pillow, so the broader V39 module could not import in that environment. The desktop already provides a Python 3.12.14 bundle with Pillow 12.3.0 and NumPy 2.3.5. Using those installed libraries required no package installation or network access.

At candidate commit `fc14994f53655da57b9b6573d028ddde1a11b858`, the bundled runtime passed the combined controller, wait/admission, soft-stale renewal, and failure-cleanup suites: **39/39 normally and 39/39 under `-O`**. The exact raw outputs are `results/bundled-39-normal.txt` and `results/bundled-39-optimized.txt`. `supplemental_audit.py` confirms the source/test hashes against `SUPPLEMENTAL_FREEZE.json` and checks the captured result shape; `SUPPLEMENTAL_SHA256SUMS` binds the supplemental records.

This closes the local Python import gap for these 39 tests. Their fixtures and extracted-closure cases remain synthetic/code-level evidence. They do not execute a live game, provider, GUI or physical input, and establish no real reaction bound, useful recovery, task effect or MAP01 outcome.
