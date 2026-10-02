# Issue #5318 — semantic serializability T0 result

## Disposition

`STOP_INDEPENDENT_AUDITOR_ORACLE_MISMATCH`. The frozen candidate completed once in Docker (exit 0) and emitted all 30 rows. The frozen independent auditor completed once but returned five reconstruction errors, all for `unknown_overlap` (one per policy). No scientific PASS/FAIL comparison is accepted. The raw, failed audit, source freeze and one-shot history are retained unchanged; no retry or post-formal source correction was made.

## H / T / D / C / U

- **H:** The hypothesis and decision gates are frozen in `PLAN.md` / `FREEZE.json`. They were not adjudicated because the raw auditor did not pass.
- **T:** Six fixed synthetic proposal pairs × five policies = 30 ordered rows: disjoint writes, trusted commuting increments, same-resource set, write-skew cycle, unknown footprint, delayed/irreversible interaction. One candidate Docker invocation, followed by one separate Docker audit invocation.
- **D:** Candidate exit 0; raw has 30 lines, 19,391 bytes, SHA-256 `26fa7c694fd0f3a35bc5085b6145af639e88c8dd79666c3284db12f11df9ed90`. Independent audit reported 30 rows and errors on all five `unknown_overlap` rows; retained in `results/formal-01/AUDIT.json`. Read-only diagnosis found the auditor's serial oracle recognizes `x-zero` / `y-zero` but not the frozen `left-zero` guard, so it reconstructs the unknown-overlap serial outcomes incorrectly. This diagnosis does not convert the failed audit into a pass; formal allocation is consumed.
- **C:** Cached `python:3.12-slim` image ID `sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`, linux/amd64; Docker Desktop `desktop-linux`; network none, one CPU, 256 MiB, 64 PIDs, read-only root and source. Host construction suite passed 6/6 after a pre-freeze implementation correction. No model/GPU, GUI, user data, network, real effects, or authority.
- **U:** Because the independent audit failed, no policy metric or hypothesis is validated. Even a future corrected successor would remain a finite abstract model only; real footprint truth, commutativity certificates, external effect receipts, compensation, fairness, and runtime safety remain untested. No rerun of this allocation.

## Frozen invocations

Formal candidate and separate auditor commands, each invoked once, used the pinned image and bounded arguments recorded in `FREEZE.json`. No retry or tuning followed the audit mismatch.

Construction: `python -B -m unittest -v test_simulator.py` — 6/6 passed before the one-shot run. The first construction attempt had 5/6 pass and was corrected before freeze; see `ATTEMPT_HISTORY.md`.
