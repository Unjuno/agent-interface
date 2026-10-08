# V39 release request ordering vs planner interrupt acknowledgement

## H / T / D / C / U

**H.** On the current V39 invalidation path, the local executor cancel request is delayed until the synchronous planner interrupt call returns. If App Server is slow to answer the interrupt request, the running cover receives no cancel request during that wait.

**T.** Freeze current `main` at `4c203d797cd3e33168bd9177fea8e0d6ef605c6b`. Read the exact V39 `cancel_invalidated_cover` helper, planner adapter `interrupt`, App Server `interrupt_turn`, and App Server `request` source by Git identity. Execute the production helper extracted from its AST through the exact adapter and client methods, with only the transport timeout shortened and the correlated response withheld. Verify whether executor cancel bytes are emitted before the transport timeout. Also run the helper with a deterministic delayed planner double and a test-only counterfactual that moves interrupt after cancel write/flush. No game allocation, model, GUI, OS input, or controller code change.

**D.** PASS_SOURCE_ORDERING_REPRODUCTION if the exact extracted helper/adapter/client methods produce `request sent → request timeout/return → executor cancel write → verified-empty terminal`, the blocked-response injection observes no cancel write, the delayed counterfactual emits cancel before entering its blocked interrupt, and source inspection confirms a 30-second default request timeout. Any contrary ordering or nonblocking interrupt behavior fails the hypothesis.

**C.** A running cover can naturally complete or expire while this happens; the controller accepts only a verified empty terminal in those cases. A fast App Server response may make this interval short in practice. Neither possibility removes the source-level dependency or quantifies actual physical hold duration.

**U.** The test uses a fake planner and process pipe. It proves message ordering and a possible wait bound in source, not how long production responses take, whether a real held key persists, how quickly the executor consumes a cancel, or whether actual key release and app effect are verified in the OS/game. It is not justification to change controller behavior ahead of the required fresh live threat exposure.

## Frozen source identities

- Main: `4c203d797cd3e33168bd9177fea8e0d6ef605c6b`
- `research/doom/map01_overlap_controller_v39.py`: `e9b437979e87347f6aa4dbefffcc84e9a2d01752`
- `research/live_control/persistent_planner_adapter_v2.py`: `1a09c8752dff6a87bf8c180cb2e6fa7f43d4ad77`
- `research/live_control/codex_app_server_client_v2.py`: `2eecb3de2d1a3d72c3276d13e148564e9c31481b`

`cancel_invalidated_cover` synchronously calls `planner.interrupt()` before writing `{"op":"cancel"}` to the local process pipe. The adapter calls `client.interrupt_turn()`. The App Server client's `request()` writes the interrupt request and waits on a condition for the correlated response; its default timeout is 30 seconds. The executed AST-isolated delay test confirms the cancel write stays absent while the current interrupt call is blocked and is emitted only after it returns. A test-only AST counterfactual moving that call after cancel write/flush emits the cancel first under the same blocked-response schedule; this is a sequencing comparison, not a deployed fix.

This establishes a code-level latency dependency worth measuring in the next authorized live exposure. A narrow candidate ordering to compare is: deliver the executor cancel first, then request planner interruption, while preserving the existing requirement to observe a verified empty terminal before proceeding. No runtime change is included here.

## Reproduce

Run `python -m unittest -v research/doom/v39_cancel_before_interrupt_ack_a01_20261008/test_order.py` and `python research/doom/v39_cancel_before_interrupt_ack_a01_20261008/audit_source.py` from the repository root. Tests read source from `HEAD` using `git show`; they write no files. The deterministic block is released by the test itself; the 50 ms fault injection validates the integrated wait/timeout path, while 30 seconds remains a source-configured default, not a measured production delay.

Construction note: the first run of the added client-timeout test errored before invoking the method because the generic extractor only searched module-level functions while `request` is a class method. The extractor was changed to locate that method in the parsed AST; the frozen target behavior was not altered. The final five focused tests then passed.

## Current-main ExecutorV13 cross-layer replay (2026-10-08)

This is an additive follow-up; it preserves the historical source identities and result above. It freezes `main` at `708ca59a8128f07fdb7e13a36704c6b2f79c9fb6`, reuses the exact current-main V39 helper, planner adapter and App Server request/interruption methods, and loads the exact current-main ExecutorV13 software stack by pinned Git blob identities in `test_handoff.py`.

The replay runs two orderings with an App Server response withheld. With the current helper, the observed sequence is `interrupt request written → interrupt response injected → cancel write/flush → ExecutorV13 input_released → terminal`. With a test-only cancel-first counterfactual, it is `cancel write/flush → interrupt request written → ExecutorV13 input_released → terminal → interrupt response injected`. In both runs the exact ExecutorV13 implementation consumes the cancel, emits its release and terminal events, and the helper observes an empty release receipt. The test pins nine executor stack modules as well as the controller, adapter, and client sources.

This is cross-layer software evidence that early executor cancellation permits the executor release path to progress while planner acknowledgement is delayed. The backend and owner are simulated: `owner_release` clears an in-memory held-key set. It does **not** establish OS-level or physical key release, live game effect, production timing, or safety under a live threat. It does not authorize changing controller behavior; the fresh live threat-exposure gate remains outstanding.

The first integrated harness attempt failed during fixture construction because the extracted current-main client method required its original timing globals and the probe's `_write` accepted a deadline keyword. The fixture was corrected without changing target sources. The final focused suite passes six tests, and the source audit confirms pinned identities and current helper ordering.

Reproduce from the repository root:

```powershell
python -m unittest -v research.doom.v39_cancel_before_interrupt_ack_a01_20261008.test_order research.doom.v39_cancel_before_interrupt_ack_a01_20261008.test_handoff
python research.doom/v39_cancel_before_interrupt_ack_a01_20261008/audit_source.py
```

Machine-readable additive result: [`CROSS_LAYER_RESULT.json`](CROSS_LAYER_RESULT.json).
