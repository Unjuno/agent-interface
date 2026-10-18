# Issue #59 — dispatch ordinary and typed observations to the pair guard (A06 construction)

## H / T / D / C / U

**H.** The A05 monitor's fallback can read signals from an ordinary full observation, but the controller wait loop dispatches only events listed in `event_types`, which omitted `observation`. The actual producer can emit a typed row and an ordinary row for one capture; dispatching both naively would treat the second row as a stale sequence and cancel an otherwise valid cover.

**T.** Add ordinary observations to monitor dispatch, exercise the reader fallback when a typed companion is absent, fail closed on reader errors, and make identical typed/full rows idempotent in either order. Mutation boundary: preserve one soft ammo event when both projections arrive for the same capture, but reject same-epoch signal/binding/frame disagreement.

**D.** PASS only if the frozen A05 monitor fails the dispatch, duplicate-epoch, and reader-error regressions; current paired controller plus existing v39, source-refresh, and immediate action-validity tests all pass; changed Python files compile; `git diff --check` passes; and freeze/artifact hashes verify.

**C.** Ordinary-image OCR can fail or disagree with typed in-memory extraction. Failures invalidate the cover; same-epoch disagreement is rejected. Repeated rows are deduplicated only for the same exact sequence/capture/binding, with compatible frame hash and paired signal contents.

**U.** This checks event-dispatch and duplicate-sample construction with synthetic readers. It does not measure live producer scheduling, cancellation timing, physical release, task effect, recovery, or MAP01. No game, GUI, model, OS input, container, or formal allocation ran.
