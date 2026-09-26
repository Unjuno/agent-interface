# #2802 Allocation 05 — actual transport drop and hidden-state provenance

Allocation: `app-transport-drop-2802-20260923-01`.

## H
A temporal consumer must distinguish an application event that never occurred from an event that occurred but was lost in transport. Source-event sequence continuity detects an actual dropped transport row; a separate application-state revision detects hidden predicate changes even when event sequence remains contiguous. Arrival delay alone must not change source-time success. Duplicate delivery is conservative UNKNOWN, not a second authoritative observation.

## T
Six scenarios x three cyclic repetitions =18 fresh producer/relay process pairs over real OS pipes: COMPLETE_AB, DELAYED_DELIVERY_B, DROP_B, HIDDEN_STATE_CHANGE, DUPLICATE_A, LATE_B. Source bound20ms. Producer writes a scoring-only truth ledger. Relay changes only delivery: delay B50ms, drop B, or duplicate A. Hidden-state case changes private state revisions twice without emitting an event, then emits a contiguous heartbeat carrying the new revision. Candidate receives only forwarded records. One formal invocation after GitHub source/hash freeze; no retry/replacement/tuning.

## D
`PASS_APP_TRANSPORT_DROP_BOUNDARY_SCOPED` requires18/18 rows and all36 child exits0; candidate SATISFIED6, EXPIRED3, UNKNOWN_GAP3, UNKNOWN_HIDDEN_CHANGE3, UNKNOWN_DUPLICATE3; unsafe timestamp-only comparator must make unsupported terminal claims in every DROP_B/HIDDEN_STATE_CHANGE/DUPLICATE_A case; delayed delivery remains SATISFIED from source time; independent raw audit errors=[] and8/8 copied-evidence corruptions reject. Missing process/truth/raw/source evidence => STOP/HOLD.

## C
Trusted single producer, one relay, one host and CLOCK_MONOTONIC. Sequence and revision fields are fixture contracts, not authentication. Hidden revision is cooperative evidence. This tests transport/state provenance, not arbitrary application semantics or causal necessity.

## U
No reconnect/wrap, multiple simultaneous obligations, hostile producer, cross-host clocks, GUI/model/task benefit, input authority, natural failure rate, tokens/latency benefit, or production promotion. Same-author separate auditor is not external human review.
