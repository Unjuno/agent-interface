# Runner compatibility check A01 (2026-10-05)

## H/T/D/C/U

- **H:** Tightening the target socket adapter to require an explicit empty release state could break the repository's existing synthetic raw-capture runner, which supplied only `{"verified": true}`.
- **T:** Called `synthetic_bridge_exchange` from `run_raw_socket_submit_construction.py`, passed its response through `TargetSocketSubmitter`, and ran the existing three-arm synthetic capture command. All work stayed in memory/local files; the bridge exchange was injected and no socket, game, model, or Docker was used.
- **D:** The regression passes only when the fixture emits the exact verified-empty release schema and the end-to-end synthetic capture completes with both audit dispositions expected for construction.
- **C:** Kept request ID, cursor progression, command receipt, authority and terminal status fixed. The fixture release object is the producer-side variable.
- **U:** This verifies only the repository's synthetic producer fixture and adapter compatibility. It does not identify or validate a live upstream runtime producer or any physical release.

## Result

The new regression first failed because `synthetic_bridge_exchange` returned only `{"verified": true}`. The fixture now emits `{"verified": true, "keys_down": [], "buttons_down": []}`. The focused regression passes. The full runner completed 12 actions per arm, 36 target dispatches, and 18 tasks, with `PASS_CONSTRUCTION_ONLY` and `PASS_SYNTHETIC_DISPATCH_JOIN`. The audit continues to report `source_identity_verified: false`; no formal source identity or allocation is claimed.

Two independent successful captures are retained in release_state_runner_compat_a02_20261005/ and release_state_runner_compat_a03_20261005/; RUNS.json records each raw digest and audit result. runner-a03-result.txt records the most recent command summary; each capture SHA256SUMS covers its evidence files. The full package now passes 123 tests in normal and optimized mode, with two expected Windows AF_UNIX skips per mode. Compile and diff checks exit 0.

No live producer implementation is present in this package: `target_execution_v1.dispatch_task_targets` receives an injected `submit` callback, and the socket adapter receives terminal JSON from its injected/Unix-socket exchange. The upstream release producer therefore remains an unverified dependency. The separate #5130 formal Docker slot is still unassigned.

After refreshing to main d12d451, the full package was rerun: 123 tests passed in both normal and optimized mode (two Windows AF_UNIX skips each); py_compile and diff checks passed. POST-MAIN-VALIDATION.json and its logs record this later validation separately from the earlier runner capture.
