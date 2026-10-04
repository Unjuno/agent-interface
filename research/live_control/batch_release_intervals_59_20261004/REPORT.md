# Current-main batch cancellation release intervals — construction report

## H/T/D/C/U

**H.** The current-main input-owner V12 can preserve a separate request-start-to-common-XSync-return bound for every key in an autonomous cancellation cleanup batch, without changing explicit-up cancellation receipts. The resulting owner-release record remains nested in Executor V13's early `input_released` event.

**T.** On the current-main lineage at branch start `5489741c1efa2d25bedf5aa64e60a68fb2f74e3c`, use fake Xlib with two held keys. Cancel the lease, observe one owner cleanup record, and independently check each keycode's ordered interval ends no later than final owner verification. Also cancel from inside the existing explicit-up XSync hook and require `cancel_requested_after_sync=true`. Pass the cancellation record through Executor V13's release-event constructor and check that the interval array is retained value-for-value.

**D.** The pre-change test must fail because `key_release_intervals_ns` is absent. The repaired current V12 owner must pass the two-key and post-sync-cancellation cases; adjacent executor, cancellation, and V4 owner-join tests must pass. Intervals are valid only as request-start through shared XSync-return bounds, with final owner keymap verification separately retained.

**C.** The array adds no per-key XSync or state query and keeps the existing single batch sync. A caller could misread a server-processing bracket as a physical key-up time; the field is intentionally limited to the client-observed XTest request / common XSync interval.

**U.** Fake Xlib only. No real X server, hardware transition, app consumption, game, model, desktop input, live allocation, policy benefit, useful-feedback timing, bounded recovery, or MAP01 outcome was tested. This does not wire session V14 into the active V39 runner and does not address scorer-event identity.

## Result and provenance

The red run on the exact pre-change current-main V12 blob `3addfe06a9d5116ec3b3d42b2ffe139885872adc` failed at the expected assertion: `key_release_intervals_ns` was absent from the cancellation record. After the owner change, the two new tests passed. Six focused test modules then passed when run in separate Python processes: the new batch telemetry test (2), explicit-up cancellation (1), Executor V13 (7), owner cancellation cause (1), publication ordering (1), and V4 owner receipt join (1), for 13 passing tests.

The direct WSL Python 3.12.3 runs used copied source from the branch and fake Xlib fixtures; no container or resource-control claim is made. A combined same-process invocation exposed pre-existing `sys.modules` fixture coupling in `test_input_transition_owner_v4`; that test passes alone, and all six modules pass in separate processes. The source change preserves the explicit-up receipt contract checked by both new and existing tests.

Candidate owner source blob: `da1a0b496572f3b853a84a94451e6824369a49b0`. New test blob: `7ce2025d2a04d28612c748d48737235e96702139`. The base V13 owner and V4 wrapper are unchanged. The only product-code change is the V12 batch cleanup record; Executor V13 already forwards the record into `input_released.owner_release`.
