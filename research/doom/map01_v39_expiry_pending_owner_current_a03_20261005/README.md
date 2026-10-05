# Current-owner V39 expiry-pending A03

This is a successor to the merged ExecutorV12 A01/A02 study. It uses the latest exact #7805 candidate InputOwner v13 blob, whose A06 change preserves per-key measurements before aggregate queries, with the same frozen bridge-v2 blob and the experimental `release_all()` final drain. The A01/A02 results remain immutable.

A03 is preserved as `STOP_CONSTRUCTION_RUNNER_ROOT_LAYOUT` (container started; candidate executions=0) because its package-only mount invalidated the runner's repository-root assumption. A04 uses a new formal run ID and repository-root mount; its no-input container preflight and independent raw-only audit passed. See `RUN.json`, `RESULT.md`, and `STOP_A03.txt`; no A03 result is inferred from the failed wrapper launch.

The distinguishing test is the boundary where `execute()` has already drained, while current-owner expiry cleanup is still blocked after fake KeyRelease/`sync()` and before publishing its owner record. It checks whether the `release_all()`-finally drain preserves that late receipt before ExecutorV12 terminal. See `PROTOCOL.md` and `SOURCE_LOCK.json` for H/T/D/C/U and exact pins.

Only fake-Xlib synthetic behavior is in scope. A pass would be a source-composition result for one forced schedule, not evidence of live X11/game input, useful task feedback, recovery, threat control, latency, MAP01 success, or Issue #59 completion.
