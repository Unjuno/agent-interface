# A07 audit-v2 correction

This correction addresses two false-PASS paths in `audit_live_v2.py`: last-row-wins maps hid duplicate terminal or input-release events, and hard-health/scorer evidence counted without proving it fell inside the decision's recorded model interval. Per-key release transitions now also have to match the admitted keys exactly.

The reconciliation requires exactly one terminal for each cancellation, rejects duplicate cancellation/release identities, accepts no-input cancellations only with no release transitions or release event and one verified empty terminal, and requires admitted keys to have matching verified transitions plus one verified empty release event. A hard-health invalidation counts only when both its monitor receipt and outcome evaluation timestamps lie in that decision's `[controller_model_started_ns, controller_model_ended_ns]` interval. Useful scorer evidence must have `observed_ns` in a recorded model interval.

`PASS` now means only that these scoped reconciliation checks passed. `formal_pass` remains false because this additive auditor does not rerun the original audit's source, stale-admission, bounded-recovery, and full preregistration gates. The original `AUDIT.json`, v1 auditor, and saved episode were not modified or rerun.

Construction regressions: `python3 -B research/doom/map01_v39_live_threat_guard_a07_20261009/test_audit_live_v2.py -v` (15 passed; the same set passes under `python3 -O -B`). These use synthetic files in temporary directories and do not inspect the saved raw episode or start the game, model, VM, or GUI.

## Follow-up false-PASS correction

A later nonauthor review of the exact PR head found two additional ways to obtain a scoped custody `PASS`: an `input_admission` with the matching key could occur after `cancel_requested` and still be counted as prior admission; and a release transition could match only the key name while its `step` or `intent_token` belonged to another actuation. Duplicate admission/transition rows with the same key-only count could also balance each other.

The follow-up now requires every admitted input to have an integer `admitted_ns` no later than the cancellation's integer `requested_ns`. It matches release transitions to unique `(step, key, intent_token)` identities rather than key names alone. New synthetic tests reject post-cancel or untimed admissions, mismatched step/token releases, and duplicate matching pairs. A valid scoped custody result continues to keep `formal_pass` false. Original raw, v1 audit, and candidate output remain untouched; no candidate or live allocation was rerun.

## Schema-type fail-closed follow-up

A synthetic malformed JSON row with an array/object in `key`, `step`, or `intent_token` previously raised `TypeError` while constructing `Counter`, before an `AUDIT_V2.json` failure result could be written. Identity fields are now type-checked before building counters. Invalid fields produce a recorded `FAIL` with identity diagnostics. The expanded synthetic suite passes 16/16 normally and under `python3 -O -B`; no saved raw allocation, game, model, VM, or GUI was used.

An additional malformed cancellation/event `id` could still raise before the audit was written because those values are used as `Counter` and `defaultdict` keys. The auditor now validates IDs for cancellation, admission, release-transition, input-release, and terminal rows before indexing, omits invalid rows from reconciliation, and records the invalid-ID count while forcing the aggregate custody result to `FAIL`. Synthetic array-ID mutations cover all five event types. The suite passes 17/17 normally and under `python3 -O -B`; raw allocation evidence remains untouched.
