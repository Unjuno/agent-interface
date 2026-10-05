# PR #7449 current-owner cancellation interleaving check C05

This one-shot construction check applies the existing frozen C02 forced queue interleaving to the exact `input_owner_v12.py` at PR #7449 head `a6da76741c91d8cfa0f035445c1fd6b8b864560e`. That PR adds explicit-key-up receipts and targets the per-key measurement gap. The check asks whether its owner release path also contains the separately demonstrated late-cancel cause fix.

## H / T / D / C / U

- **H:** PR #7449's current owner records ordinary `release` when cancellation becomes visible after the explicit release request is dequeued but before dispatch; the ordinary-release control remains ordinary.
- **T:** Freeze the exact PR source blob and frozen C02 test bytes. Run that test once with `OWNER_UNDER_TEST` pointing to the frozen PR-source snapshot. Do not modify the PR branch or retry.
- **D:** PASS for this hypothesis if the cancellation test fails specifically because actual cause is `release` instead of `cancelled`, while the ordinary-release control passes. This is a finding of an unfixed defect in that source snapshot, not a candidate-fix PASS.
- **C:** This executes the actual owner thread with fake Xlib and a forced deterministic queue order. It does not run the PR #7449 release batch backend, ExecutorV12, v14 session, X server, or game.
- **U:** No real X11 schedule, physical release, useful task feedback, recovery latency, live MAP01 behavior, or main integration is measured.

See `FREEZE.json`, `PR-SOURCE-input_owner_v12.py`, raw output, exit receipt, and independent audit. It is evidence for reconciling the overlapping PR stack, not a new allocation.
