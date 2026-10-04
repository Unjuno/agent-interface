# PR #7449 cancellation-cause integration C06

C05 showed that exact PR #7449 head `a6da76741c91d8cfa0f035445c1fd6b8b864560e` still misclassified the after-dequeue cancellation race while its ordinary-release control passed. This C06 candidate adds the cause-selection condition to that PR's richer owner v12, preserving its explicit key-up history, and tests both the frozen C02 owner case and ExecutorV12 publication through the actual transition-owner v4 wrapper.

## H / T / D / C / U

- **H:** On the PR #7449 owner foundation, explicit cleanup after cancellation/dequeue will retain cause `cancelled` without breaking ordinary release, explicit key-up receipts, or lease-bound ExecutorV12 release publication.
- **T:** Freeze the owner/backend/executor/wrapper and both tests. Run the two-case forced owner-interleaving test once with the patched v12 source, then run the integrated owner→transition-wrapper→ExecutorV12 test once. Preserve raw stdout and separate exit receipts.
- **D:** PASS requires both tests to exit zero; C02's cancellation and ordinary controls both pass; the integrated publisher emits a verified-empty `input_released(reason=cancelled)` before `terminal(status=cancelled)`; the fake display sees key press/release.
- **C:** The integration uses fake Xlib and a minimal backend. The extra owner key-up history code is present but the forced cancel case uses explicit owner cleanup, not a full release-batch execution. Existing PR #7449's own focused batch tests remain separate evidence.
- **U:** No full v14 session/backend runtime, X server, game, model, independent useful task effect, bounded recovery, matched benefit, or live MAP01 allocation is measured.

C05 retains the source-bound pre-fix reproduction. C06 is construction evidence only and does not consume or replace the gated live experiment. Raw, source freeze, and independent audit are in this directory.

## Result

PASS. The frozen cancellation/ordinary-release pair passed 2/2, and the actual ExecutorV12→transition-v4→v12-owner integration passed 1/1. The audit confirms the patched v12 is exactly one cause-selection delta from PR #7449's source, retains the explicit-key-up implementation unchanged, and publishes the verified-empty `input_released` event before the cancelled terminal event. After merging #7449's latest parent-composition update at `38f48ea7f1`, the current-stack regressions passed: transition owner v4 1/1, backend v3 composition 2/2, actual composition 4/4, and ExecutorV12 2/2 (9 total). C05's expected pre-fix defect reproduction and source audit pass.
