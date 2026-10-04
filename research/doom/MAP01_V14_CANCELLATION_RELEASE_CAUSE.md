# MAP01 v14 cancellation-aware release cause

## H / T / D / C / U

- **H:** When lease cancellation becomes visible after the v10 owner loop's cancellation precheck and after it dequeues the worker's explicit `release`, the v10 owner records a verified release as ordinary `release`. A versioned owner can preserve `cancelled` as the cleanup cause without changing ordinary-release behavior.
- **T:** Force that queue ordering through the actual current-main owner thread using an in-process queue hook and fake Xlib state. Compare exact current-main `input_owner_v10.py` with additive `input_owner_v12.py`; keep an ordinary-release positive control.
- **D:** The parent reports `release` for the forced cancellation case while the positive control reports `release`. The candidate reports `cancelled` for that same forced cancellation case, retains `release` for the positive control, and verifies empty key state in both. Static source audit confirms the candidate differs from v10 only at the release-cause selection. The opt-in v14 session selects the v4 backend, which selects transition owner v4 over input owner v12.
- **C:** This executes the actual owner request thread and X11 call sites under fake Xlib with a controlled queue schedule. It does not execute the historical v39 `ExecutorV12` worker/finally or `_publish_release` chain; the test isolates the lower-layer defect and fix.
- **U:** No X server, physical device input, game, model, independent useful task feedback, bounded-recovery timing, matched benefit comparison, MAP01 outcome, or formal/live allocation. No input beyond a fake in-memory X11 display.

## Result

C01 on exact current-main v10 produced the predicted false classification (`release`) after cancellation arrived between dequeue and dispatch; the ordinary control passed. Its independent audit passed all seven checks. C02 on additive v12 passed both cases: cancellation was preserved as `cancelled`, ordinary release remained `release`, and each emitted one verified-empty release record. The v12 source is a byte-identical copy of v10 except for release-cause selection.

This supports integrating the cancellation-cause repair into an opt-in current-main session version. It does not establish that the higher-level v39 terminal event publishes an `input_released` receipt or that the live MAP01 path is repaired end to end. A fresh integrated construction or separately allocated live study is still required for those claims.

## Owner-to-executor construction integration (C03)

A subsequent local integration regression joins the actual `ExecutorV12` implementation and `_publish_release` watcher with the actual v12 owner request thread through transition-owner v4. A minimal backend calls the wrapper for a held key and final release; fake Xlib records the physical-state transition. The forced cancellation schedule makes cancellation visible to the executor immediately but only to the owner's release dispatch after dequeue, preserving the target interleaving deterministically. It passes: a verified empty-state `owner_release(reason=cancelled)` becomes `input_released` before the `terminal(status=cancelled)` event, and the fake display observes key press then key release. The existing ExecutorV12 unit regression also passes 2/2, and the C02 12-check source/raw/wiring audit remains green.

This closes the specific construction gap between the owner cause and executor publication and includes the v4 owner wrapper. Evidence is in [`results/map01-v39-cancel-release-cause-integration-v1/`](results/map01-v39-cancel-release-cause-integration-v1/), with source/output SHA-256 manifest. This is a local non-formal regression using fake Xlib and a minimal backend. It still does not run the complete v14 session/backend in a live MAP01 allocation or establish application effects, useful feedback, bounded recovery, or comparative benefit; Issue #59 remains unresolved.

## Reproduction and evidence

Run `python -B test_cancel_release_cause.py` from either C01 or C02's result directory. C01 uses `input_owner_v10.py`; C02 sets `OWNER_UNDER_TEST` to `research/live_control/input_owner_v12.py`. C01 and C02 retain their own FREEZE, raw output, exit receipt, and audit. No retries were made.
