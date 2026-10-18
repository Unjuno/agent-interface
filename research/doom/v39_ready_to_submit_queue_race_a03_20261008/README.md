# V39 ready-to-submit observation ordering A03

This synthetic source-slice check asks whether a typed observation queued after completion-drain readiness is discarded by the executor-acceptance wait. It parses the frozen V39 caller and executes its exact nested production `wait` function against a deterministic fake queue. No executor binary, GUI, game, OS input, or live allocation is used.

Harness construction STOPs A01 and A02 are retained as sibling `A01_INITIAL_FAILURE.txt` and `A02_INITIAL_FAILURE.txt` records. A03 is the first completed trace.

## H / T / D / C / U

- **H:** After `prepare_action_admission` returns `READY_FOR_FRESH_EXECUTOR_ADMISSION`, a newly queued typed observation can be consumed by the first executor-acceptance wait without being delivered to the running-action monitor.
- **T:** Freeze current-main controller source; AST-check readiness, submit, the unmonitored acceptance wait, and the later monitored terminal wait; execute the exact production `wait` helper against typed health 100→70 followed by a fake acceptance event.
- **D:** Record `PASS_TYPED_OBSERVATION_DROPPED_AT_ACK` only if the helper returns acceptance, consumes the typed row without a monitor call, and leaves no row queued.
- **C:** This establishes queue-consumer behavior for the fixed synthetic ordering, not whether the game executor accepted or emitted any input before a real invalidation.
- **U:** No live threat, observation cadence, queue-reader scheduling distribution, executor acceptance, input, physical release, recovery, progress, or task outcome is measured.

## Reproduction

```text
python -m research.doom.v39_ready_to_submit_queue_race_a03_20261008.candidate
python -m research.doom.v39_ready_to_submit_queue_race_a03_20261008.audit
python -m unittest -v research.doom.v39_ready_to_submit_queue_race_a03_20261008.test_audit
```
