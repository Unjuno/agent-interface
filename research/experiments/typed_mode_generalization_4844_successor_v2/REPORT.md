# #5184 fresh-seed typed-mode successor

## Current status

Allocation `typed-mode-4844-successor-20260928-02` is frozen for one local Docker Desktop formal run, pending exact-source commit and preflight. **No formal runner or auditor invocation has occurred.** No quality or efficacy result is available.

### Preserved predecessor failures

- #4844 allocation `typed-mode-4844-seed-484401-v1`: `STOP_PROVENANCE_OR_AUDIT`; its 3,000-row metrics remain exploratory and do not adjudicate the hypothesis.
- A conflicting #4844 comment reports a 4,800-row `FAIL_MODE_MISROUTES_RECOVERY`, but links to #4155's different evidence path and seed family. It is not pooled or used as a formal result here.
- Successor allocation -01: `STOP_PREFORMAL_SEED_EXPOSURE`. A Stage-0 test accidentally ran the full generator with candidate seeds 484411/484412 before freeze. It did not run in Docker, persist raw output, or produce a retained numerical estimate. Those seeds are retired, recorded in Issue #5184, and are not reused.

## H / T / D / C / U

See [PLAN.md](PLAN.md) for the complete frozen hypothesis, exact schedules, decision gates, confounders, and scope limits. Current Stage-0 uses only seeds 17001/17002, disjoint from all formal allocations.

## Stage-0 result

On Windows 11 / CPython 3.12.10, `python -B -m unittest -v test_stage0.py` passed **6/6**. Tests verify the 4,800-row accounting on construction-only seeds, 960 rows per block and 192 per mode, full-observation and unknown controls, 16 evidence mutation rejections, canonical raw serialization, duplicate-key rejection, and frozen source digests/sidecar. `py_compile` passed. This is construction evidence only; no formal metrics are reported.

Docker Desktop `desktop-linux` reports Engine 28.5.1 linux/x86_64 and an empty running inventory. The selected cached pinned image `sha256:1aaa65a85fda306ffb8b910824d4e93bdce61e212c7e87168123ea3073b41a1a` was launched once in a bounded no-network/read-only smoke check and reported CPython 3.12.14; the container exited and the inventory returned empty. This is environment readiness, not the formal experiment.

## Frozen source and next formal boundary

`FREEZE.json` binds each stage-0/formal source by Git blob, SHA-256, and bytes. `FREEZE.sha256` binds the freeze document. Formal execution may begin only after the committed source tree re-verifies exactly, the current remote main still equals the registered intake, Desktop context/image/inventory gates pass, and both unique output directories are absent. The frozen one-shot runner and separate raw-only auditor commands are recorded in the freeze. Preserve runner stdout/stderr, raw bytes/hash, audit stdout/stderr/receipt, exit codes, and exact container identity. Never retry or silently relabel a pre-result STOP.
