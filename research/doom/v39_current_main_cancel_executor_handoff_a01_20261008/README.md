# V39 current-main cancel-first ExecutorV13 handoff replay (A01)

This deterministic cross-layer construction replay checks the current-main `cancel_invalidated_cover` and `PersistentPlannerAdapter.interrupt` path while an App Server interrupt response is withheld. It uses exact current-main controller, planner-adapter, and App Server client source snapshots from `24319711a2b4f8c782c2648522f30dc70b4c9b09`, plus the retained nine-module ExecutorV13 software stack pinned at `708ca59a8128f07fdb7e13a36704c6b2f79c9fb6`. The prior A01 handoff harness is also bundled and identity-pinned; this package invokes its event fixture with the actual current-main helper, not the old helper or the earlier test-only counterfactual.

## H/T/D/C/U

- **H:** The current helper sends and flushes the Executor cancel through `before_transport` before the synchronous App Server interrupt request. The ExecutorV13 software stack can consume that cancel, publish `input_released`, and emit a verified empty terminal before the interrupt response arrives.
- **T:** Extract the exact frozen current-main helper, planner adapter, and client request methods; run them with the exact pinned ExecutorV13 stack and a deterministic App Server probe that withholds its response until the Executor terminal appears.
- **D:** PASS only if the event trace has cancel write and flush before App Server request, and both `input_released` and the verified empty terminal before response injection; the helper must return that empty receipt.
- **C:** One controlled schedule shows that this path is possible. A production response may be fast; a simulated backend cannot measure real key hold or system behavior.
- **U:** The ExecutorV13 modules are the retained 708 snapshot and are not asserted to be the current production runtime stack. No OS-level or physical release, live threat response, production timing, independent task feedback, recovery, or task effect is established.

## Result

`PASS_CURRENT_MAIN_HELPER_CROSS_LAYER_RELEASE_BEFORE_INTERRUPT_RESPONSE`. The observed order was `accepted → step_started → controller_cancel_write → cancel_requested → controller_cancel_flush → appserver_interrupt_request_written → input_released → terminal → appserver_interrupt_response_injected`. The in-memory owner ended with no held keys, and the helper returned a verified empty release receipt. Source hashes and the event ordering pass the independent audit in `AUDIT.json`.

This is software-composition evidence only. It does not replace the still-required live threat exposure. No runtime change, planner call, GUI, game allocation, or OS input was used.

The first harness attempt stopped before constructing ExecutorV13 because the WSL clone could not resolve its Windows-style Git alternate-object path. That fixture retrieval failure is retained in `FIXTURE_ATTEMPT_01.json`. The nine frozen ExecutorV13 source files and event harness were then bundled and hash-checked; the unchanged scenario passed on the repaired fixture.

## Reproduction

From repository root on Ubuntu WSL:

```sh
python3 -B research/doom/v39_current_main_cancel_executor_handoff_a01_20261008/run_candidate.py
python3 -B -m unittest -v research.doom.v39_current_main_cancel_executor_handoff_a01_20261008.test_current_handoff
python3 -B research/doom/v39_current_main_cancel_executor_handoff_a01_20261008/audit_source.py
```

`FREEZE.json` pins all production source snapshots and the ExecutorV13 stack. The run uses no local Git object lookup, so it remains reproducible in WSL checkouts that cannot resolve Windows-style alternate object paths.
