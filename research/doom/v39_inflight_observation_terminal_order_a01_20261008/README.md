# V39 in-flight observation versus terminal boundary (A01)

## H/T/D/C/U

- **H:** If the stdout reader has decoded a hard-invalidating observation but has not yet queued it when the completed-future snapshot runs, the controller's subsequent terminal wait still observes it before a matching cover terminal, interrupts the planner, and discards the completed answer.
- **T:** Run the exact current-main `drain_pending_observation_events` and nested `wait` functions under a deterministic threaded queue schedule. Hold a decoded observation outside the queue during the bounded snapshot, then enqueue it before the cover terminal. Use a synthetic monitor and verified-empty terminal.
- **D:** PASS if the snapshot sees no event, the subsequent wait returns `policy_invalidation` before the matching terminal, and the dependent answer is discarded after an empty release terminal.
- **C:** One controlled schedule tests source composition, not production thread timing or event delivery. The conclusion depends on observation and terminal lines retaining FIFO order on the same stdout stream.
- **U:** Current Executor/backend output serialization for observations was not exercised. No game, model, GUI, OS input, physical release, real latency, useful feedback, bounded recovery efficacy, or task effect was measured.

## Result

`PASS_INFLIGHT_OBSERVATION_INVALIDATES_BEFORE_TERMINAL`. The future-completion snapshot returned empty while the reader held the already-decoded observation. After release, the exact current-main `wait` dispatch processed the health-60 sample, returned a policy invalidation, and retained the latest observation; the matching cancelled terminal carried verified empty keys/buttons. The harness therefore rejected the completed answer. The candidate AST-extracts the current-main final-admission helper and decision functions; the source/event audit and focused test pass.

This is distinct from PR #8431 and PR #8435: those exercise observations already in the reader queue at completion, while this test holds a decoded line outside the queue during the snapshot and delivers it afterward. It tests the next scheduling boundary after the bounded queue snapshot. It narrows the implementation risk conditionally: with same-stream FIFO delivery, the ordinary wait path covers this event. Before claiming the producer ordering invariant, verify the actual current runtime event writer or collect live traces. No production code changed.

## Reproduction

From the repository root on Ubuntu WSL:

```sh
python3 research/doom/v39_inflight_observation_terminal_order_a01_20261008/run_candidate.py
python3 -m unittest -v research.doom.v39_inflight_observation_terminal_order_a01_20261008/test_inflight_order.py
python3 research/doom/v39_inflight_observation_terminal_order_a01_20261008/audit_result.py
```

`FREEZE.json` pins the current-main commit and controller Git blob; the test AST-extracts the production helper and nested wait function from the bundled source snapshot.
