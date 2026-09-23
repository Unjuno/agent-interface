# Bounded applied-intent history v1

Task: `COORD-BOUNDED-INTENT-HISTORY-20260917-021`

Decision: **`PASS_BOUNDED_APPLIED_INTENT_HISTORY_SCOPED`**

## Method

Container-first deterministic state-machine experiment. GitHub was not the measured state machine; it is only the canonical publication surface. Exact source bytes were SHA-256 frozen locally before execution. The formal runner was invoked once.

## First outcome

| Case | Outcome |
|---|---|
| single slot, A then B, recover A | `UNKNOWN_INTENT_NOT_RETAINED` |
| capacity-2 history, A then B, recover A | `ALREADY_COMMITTED_SELF` |
| capacity-2 history, query A with altered transition content | `CONFLICT_INTENT_CONTENT` |
| capacity-2 history, A then B then C, recover A | `UNKNOWN_INTENT_EVICTED` |
| capacity-2 history after A/B/C, recover B | `ALREADY_COMMITTED_SELF` |

The eviction classification is derived from the retained generation horizon; the fixture does not keep an unbounded intent-ID tombstone set.

## Container checks

- `python -m py_compile model.py test_model.py run_experiment.py verify.py`: PASS
- `python -m unittest -v test_model.py`: 5/5 PASS
- formal runner invocation count: 1
- `verify.py`: `PASS_VERIFY`
- formal reruns: 0

## Interpretation

A single `last_applied_transition` slot loses recovery evidence as soon as a later legitimate transition overwrites it. A bounded history of two content-bound receipts preserves the immediately older intent without weakening same-ID/different-content conflict handling. The same bound also creates an explicit finite recovery horizon: after a third transition, A is outside the retained window while B remains recognizable.

## Boundary

Deterministic single-process container fixture only. Capacity 2 is illustrative, not an optimized retention policy. No crash/power-loss durability, authentication, distributed consensus, simultaneous linearizability, external effects, storage/latency benchmark, or production exactly-once claim.

## Next question

Keep bounded content-bound history fixed and vary only expiry/garbage-collection semantics. Test whether an expired intent ID can be safely distinguished from a genuinely new intent without retaining unbounded tombstones.
