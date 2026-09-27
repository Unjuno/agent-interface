# Calibrated capture-to-controller clock translation at the running-action guard

## H/T/D/C/U

- **H:** The raw container capture timestamp compared with a host decision appears over 30 seconds old. Translating that capture using the conservative lower bound of a same-session host-minus-container calibration should restore valid freshness; a timestamp deliberately shifted 31 seconds older should still be rejected.
- **T:** One persistent pinned linux/arm64 container; three host-before/container/host-after monotonic-clock brackets. Use the exact main-branch action-validity validator and RunningActionGuard. Run isolated raw, conservatively translated, and 31-second-older controls. No Executor action is sent; only guard receipts are inspected.
- **D:** PASS only if raw mixed-domain input becomes `REJECTED_STALE/CANCEL_REQUIRED`, translated current capture becomes `VALID_CURRENT/INPUT_ACTIVE` within the 30-second limit, and the older control remains `REJECTED_STALE/CANCEL_REQUIRED`. Actual result met all three. PASS is scoped to the measured host/container pair and fixture.
- **C:** Image `issue2679-map01-runtime@sha256:029e1867aeb843f2d63080343bfbb61540b64852ce00d4d99ec0be51796a093e`, linux/arm64, `--network none --read-only`, 16 MiB no-exec tmpfs. Exact source blob IDs and SHA-256 digests are in `result.json`. No model/game/GUI/physical input/formal allocation. `INPUT_ACTIVE` is a guard-state receipt, not evidence that physical input was active.
- **U:** Does not recover seed-990641's missing operands or prove its clock source, does not verify real Executor admission/release, and does not establish MAP01 task effect or runtime patch safety.

The initial harness's lost-output HOLD remains recorded on Issue #4544. The corrected run below is a new construction invocation; no scientific outcome was assigned to the failed harness.