# Epoch-fenced event resync after critical-event overflow

Task: `EVENT-RESYNC-EPOCH-20260917-003`

Decision: **`PASS_EPOCH_FENCED_EVENT_RESYNC_SCOPED`**.

## Question

After a bounded critical-event backlog enters `RESYNC_REQUIRED`, does a fresh current-state snapshot justify erasing the historical event gap, or should event completeness restart under a new epoch while the old gap remains explicit?

## Container-first method

The experiment used a deterministic pure-Python state machine with event capacity 4. Construction finished before freeze with `py_compile` PASS and 9/9 unit tests PASS. The exact source/cases/plan bytes were then SHA-256 frozen. The formal runner was invoked exactly once. `verify.py` returned `PASS_VERIFY`; all six frozen source hashes matched after the result; formal reruns were 0.

## Result

The negative-control `naive_clear_on_snapshot` overflowed after ten critical events. Six event payloads were therefore never retained. A fresh snapshot at sequence 12 then cleared the active overflow in the same event epoch and reported `coverage_complete=true`, while retaining no historical-gap marker. Current state was fresh, but event-history completeness was false.

The candidate `epoch_fenced_resync` used the same overflow and current snapshot but:

- advanced `event_epoch` **1 -> 2** exactly once;
- retained a bounded historical-gap receipt for prior epoch 1;
- preserved `first_unretained_seq=6`, `first_unretained_event_id=A-e5`, kind `TERMINAL`, and `unretained_count=6`;
- installed the current state at snapshot sequence 12;
- cleared the active overflow only for the new epoch;
- granted no input authority.

After resync, three new critical events (`A-new-e1..e3`) plus ordinary state through sequence 16 were ingested. New epoch 2 remained `coverage_complete=true`, retained all three new events, and left the prior historical gap byte-for-byte unchanged.

Frozen negative controls also passed:

- stale snapshot -> `STALE_RESYNC_SNAPSHOT`, state unchanged;
- wrong overflow identity -> `RESYNC_OVERFLOW_MISMATCH`, state unchanged;
- wrong session -> `RESYNC_SCOPE_MISMATCH`, state unchanged;
- no active overflow -> `RESYNC_NOT_REQUIRED`;
- exact replay of the accepted resync -> `ALREADY_RESYNCED_SELF`, no second epoch advance.

All ten formal gates passed.

## Interpretation

A fresh current-context snapshot can restore *current state*, but cannot reconstruct transient event payloads that were never retained. Treating that snapshot as proof that the old event epoch is complete creates a false continuity claim.

A small epoch fence separates the two statements:

1. prior epoch contains an explicit historical gap; and
2. future event coverage is complete from a new checkpoint onward.

This is compatible with observation-only recovery: seeing current context still grants no input authority and does not rewrite event history.

## Boundary

This deterministic fixture does not implement full-trace recovery, semantic reconciliation of lost events, planner attention savings, delivery retry, ACK/resolution, priority/batching, disk durability, model/GUI behavior, or task correctness. It proves only the scoped continuity rule for one overflow-to-resync transition. Multiple historical gaps and long-term compaction are not promoted by this result.
