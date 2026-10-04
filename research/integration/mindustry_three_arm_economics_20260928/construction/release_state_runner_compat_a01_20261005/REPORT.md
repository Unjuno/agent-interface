# Runner compatibility check A01 (2026-10-05)

## H/T/D/C/U

- **H:** Tightening the target socket adapter to require an explicit empty release state could break the repository's existing synthetic raw-capture runner, which supplied only `{"verified": true}`.
- **T:** Called `synthetic_bridge_exchange` from `run_raw_socket_submit_construction.py`, passed its response through `TargetSocketSubmitter`, and ran the existing three-arm synthetic capture command. All work stayed in memory/local files; the bridge exchange was injected and no socket, game, model, or Docker was used.
- **D:** The regression passes only when the fixture emits the exact verified-empty release schema and the end-to-end synthetic capture completes with both audit dispositions expected for construction.
- **C:** Kept request ID, cursor progression, command receipt, authority and terminal status fixed. The fixture release object is the producer-side variable.
- **U:** This verifies only the repository's synthetic producer fixture and adapter compatibility. It does not identify or validate a live upstream runtime producer or any physical release.

## Result

The new regression first failed because `synthetic_bridge_exchange` returned only `{"verified": true}`. The initial fixture update supplied the two empty held-input arrays, and captures a02/a03 passed with the minimal safe envelope. Subsequent source-path inspection showed that the real producer returns four additional fields. The adapter now validates and accepts that named metadata envelope while rejecting unknown fields; the synthetic fixture was updated to match the source shape.

Capture a04 exercises this source-shaped record end-to-end: 12 actions per arm, 36 target dispatches, and 18 tasks, with `PASS_CONSTRUCTION_ONLY` and `PASS_SYNTHETIC_DISPATCH_JOIN`. The full package passes 124 tests in normal and optimized mode, with two expected Windows AF_UNIX skips per mode. `PRODUCER-COMPAT-VALIDATION.json`, `runner-a04-result.txt`, and `PRODUCER-CONTRACT-REVIEW.md` record test results, source hashes and contract evidence. All three retained capture manifests verify. The audit reports `source_identity_verified: false`; no formal source identity or allocation is claimed.

The live producer source is present under `research/live_control`: the Mindustry child selects `mindustry_receipt_session_v1.Backend`, which inherits the `session_v5.release_all` path and returns the `input_owner_v10` record through `executor_v3`. `PRODUCER-CONTRACT-REVIEW.md` records the source path. This code was inspected but never executed against X11/game input; runtime behavior remains unverified. The separate #5130 formal Docker slot is still unassigned.

After refreshing to main d12d451, the package passed 123 tests before the producer-envelope additions. The later 124-test verification against the same main is recorded separately in `PRODUCER-COMPAT-VALIDATION.json`. POST-MAIN-VALIDATION.json and its logs record this later validation separately from the earlier runner capture.

The repository advanced again to main c99d93a while this PR was being prepared. After merging it, all 124 tests passed in both modes and source-shaped capture a05 passed both construction audits. `LATEST-MAIN-VALIDATION.json` preserves these results and verifies all retained capture manifests.
