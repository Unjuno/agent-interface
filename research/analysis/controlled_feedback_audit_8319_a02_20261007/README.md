# Issue #8327 — audit-only successor for Issue #8319 A01

This package independently checks the immutable 400-row A01 factorial raw. It does not rerun the candidate, change the A01 raw, repair the A01 result, or infer a human/researcher effect.

See `FREEZE.json`, `RUN_RECORD.json`, and `REPORT.md` for the frozen audit contract and one-shot result. The audit input is copied byte-for-byte from A01 and pinned by SHA-256. The auditor imports neither A01 source module.

Construction command: `python3 -m unittest -v test_auditor.py` (run from this directory). Formal command: `python3 auditor.py inputs/a01_candidate.json results/audit.json` (one invocation after freeze; no retries).

Runtime: standard-library Python on macOS arm64. This pure CPU audit does not require a container and makes no isolation claim.
