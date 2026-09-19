# Producer quiescence retry experiment

This directory retains the frozen plan, exact measured Python sources, result, validation summary and report for Issue #253.

The live experiment used two pinned local FFmpeg inputs and a private Xvfb/xterm started by real XTEST Return. The binary fixtures and full per-case evidence are not stored byte-completely in GitHub; their SHA-256 identities were frozen before measurement in `FREEZE.json` / `plan.json`, and the complete conversation archive is recorded in `archive.json`.

Decision: retain a **scoped reap-before-same-target-retry gate**. In the frozen 16-case block, immediate retry produced a completed B artifact in every case but later reverted to predecessor A in 6/8 cases. Waiting for A to reap before B produced final B in 8/8 cases. This is a correctness/latency trade-off, not a speedup or generic exactly-once claim.

`audit.py` is the premeasurement frozen independent auditor and uses a stdlib PNG decoder. `test_audit.py` was added post-hoc and requires the retained raw evidence via `PRODUCER_QUIESCENCE_EVIDENCE_ROOT`.

Do not rerun consumed IDs. A new live experiment requires a new allocation, source freeze and output directory.
