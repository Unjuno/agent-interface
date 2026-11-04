# G10 evidence and current-main reuse crosswalk

Date checked: 2026-11-03. This is a read-only source/evidence comparison. It does not replay G10, invoke Calc, allocate a live run, or establish WSLc/MAP01 readiness.

## Existing evidence that can be reused

The retained archive at `research/integration/calc_current_shared_3311_4d74_20261004/calc-compiled-ocrlive-4d74/` reports one fixed-geometry/font Calc run with two guarded saves, three capture-time-bound graph observations, seven retained OCR attempts, native receipts with verified empty releases, external neutral-state observations, and independent saved-XML scoring of values/formulas. The report explicitly limits this evidence: primary model usage is UNKNOWN; it is not a matched efficiency/reliability comparison, broad OCR validation, or cold/warm/invalidation/repair study. Reuse the raw images, receipts, OCR transcript, saved files, and auditor result only for those stated claims.

The archived source snapshots are not interchangeable with current-main code. For the following paths, Git blob IDs in the G10 `sources/` snapshot differ from `origin/main`: `runtime/core_v1/compiled_gui.py` (archive `ca14d654a758`, main `5b35baa5fab3`); `runtime/guarded_x11_v1/bridge.py` (`42466a34b631`, `b6c39f9c2c78`); `runtime/backends/x11_v1/backend.py` (`0b168d6e8b84`, `2302da74fbab`); `runtime/backends/x11_v1/session.py` (`4dbd6dd219e2`, `e518c0bada23`); `runtime/cli_v1/api.py` (`a74962ceaf63`, `8ace61ce043f`); `runtime/cli_v1/observe.py` (`82a95451bf9d`, `8b49f12aba15`); and Win32 backend/session (`e90a08b35c04` vs `2b0ae03818d9`, `8774d2a41083` vs `9f694771fc62`). `runtime/selector_v1/selector.py` is identical (`16c899456917`). These abbreviated Git object IDs make the comparison reproducible against the preserved tree; inspect full object IDs with `git rev-parse` when selecting code for an implementation.

## Current composition seam and gaps

Current `research/live_control/integrated_efficiency_compiled_execution_v2.py` exposes `run_compiled_interface_in_caller(..., on_receipt=...)`. It retains a detached receipt in the returned caller result and can publish a copy through `on_receipt`; its docstring states that an in-memory receipt does not guarantee durability or release. A sink exception skips outer verification and records `CALLER_FAILED`, preserving known input progress. This is useful composition infrastructure, but it is not evidence that the Calc caller durably captures receipts or independently verifies physical input state.

The current prototype in this directory composes lifecycle cleanup and audit callbacks, but its README correctly says the audit/release claim is trusted input. Its tests use fake WSLc transport and synthetic release/effect receipts. Do not use those tests or G10's X11 native receipts as proof of current-main Win32/WSLc delayed-input recovery.

The concrete missing composed-path check is a fresh, prospectively specified Calc caller that persists every compiled receipt and per-attempt cost before outer verification, binds source freshness and observation IDs, independently measures key/button neutrality after normal and delayed/expired actions, and scores saved bytes independently. The matched design must account for every attempt (including setup, OCR/native calls, timeout, recovery and unknown outcomes) across cold, warm, invalidation and repair conditions. G10 can qualify narrow adapter behavior and scoring fixtures; it cannot supply the new experiment's outcomes or accounting retrospectively.

## Next evidence gate

Before any new live run, freeze the exact caller/source hashes, target and allocation, same-model arms, repetitions, warm/cold state transitions, stale-evidence and expiry injections, recovery deadline, physical-neutrality oracle, saved-file oracle, complete raw schema, and all-attempt efficiency/correctness denominators. If any arm, task result, release state, or model usage is unknown, preserve it as unknown and include it in the attempt accounting. Keep the full comparison open until those raw records and an independent audit agree.
