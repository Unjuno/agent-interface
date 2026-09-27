# Fail-closed critical-event backlog overflow v1

Task: `EVENT-BACKLOG-OVERFLOW-20260917-002`

Decision: **`PASS_FAIL_CLOSED_EVENT_OVERFLOW_SCOPED`**

## Question

With the split latest-state / retained-critical-event semantics from #658 held fixed, compare a bounded event queue that silently drops oldest events against a bounded queue that fails closed with explicit overflow evidence when the planner remains absent.

## Frozen mechanism

Per-session critical-event payload capacity is **4**.

- `unbounded_reference`: all event payloads retained.
- `drop_oldest`: newest four event payloads retained; older payloads silently evicted while `coverage_complete=true` remains asserted.
- `overflow_fail_closed`: first four event payloads remain immutable. The first additional event creates one bounded `RESYNC_REQUIRED` receipt with first unretained sequence/kind and `unretained_count`; later events only increment that count. Ordinary latest-state replacement continues independently.

No ACK, resolution, priority, batching, delivery retry, disk durability, automatic input or planner action is in this rung.

## Container-first execution

- `py_compile`: PASS
- deterministic unit tests: 8/8 PASS
- formal runner: exactly 1 invocation
- formal reruns: 0
- `verify.py`: `PASS_VERIFY`
- post-result source SHA-256 recheck: 6/6 PASS

## First outcome

| Case | Reference | drop-oldest | overflow-fail-closed |
|---|---|---|---|
| below capacity (3 events) | 3 retained | 3 retained, healthy | 3 retained, healthy |
| exact capacity (4) | 4 retained | 4 retained, healthy | 4 retained, healthy |
| overflow once (5) | 5 retained | e1 silently lost | e1..e4 retained; e5 starts `RESYNC_REQUIRED` |
| overflow many (10) | 10 retained | only e7..e10 retained, still claims complete | e1..e4 retained; first unretained seq5; count6 |
| state after overflow | event overflow + 100 state updates | oldest event silently lost | overflow identity unchanged; latest state advances to seq105 |
| cross session | A overflows; B below capacity + state storm | A silently loses event; B stays separate | only A overflows; B remains healthy; state remains session-scoped |

Across the authored matrix, `drop_oldest` silently loses **9** critical-event payloads while continuing to claim complete coverage.

All candidate event payload lists stay at or below capacity 4. Existing retained payloads are never evicted. Every unretained event is represented by an explicit incomplete-coverage state; the candidate does **not** claim that the lost payload history remains reconstructible.

## Interpretation

A bounded critical-event queue cannot both retain arbitrary event history and use bounded memory while the planner is absent indefinitely. The scoped correctness property is therefore not “never lose any event payload”. It is:

> once full fidelity can no longer be guaranteed, the interface must stop claiming complete event coverage and surface a bounded fail-closed resynchronization requirement instead of silently overwriting prior critical transitions.

This preserves the state/event distinction from #658: ordinary state can keep coalescing to the newest per-session value after critical-event overflow without altering the retained event prefix or the overflow identity.

## Boundary

The fixture is deterministic and single-process. Critical-event classification is authored. `RESYNC_REQUIRED` is only a typed boundary; no resync mechanism is tested here. This does not establish planner/token savings, real watcher correctness, ACK/resolution behavior, priority/fairness, delivery latency, storage durability, or a production queue policy.

A useful successor, only if demanded by integration, is a bounded resync protocol that restores complete current context after overflow without treating missing historical event payloads as acknowledged/resolved.
