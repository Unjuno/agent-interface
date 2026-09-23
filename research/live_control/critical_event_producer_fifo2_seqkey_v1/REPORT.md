# Sequence-keyed FIFO2 repair — retained result

Task `CRITICAL-EVENT-PRODUCER-FIFO2-SEQKEY-20260917-004`, Issue #742. Immutable publication BASE `95bb57c4d651e5664fb5bbc7c79e50e852777f72`.

## Decision

**`PASS_SEQUENCE_KEYED_FIFO2_SCOPED`.**

Direct repair successor to #731. The only scientific factor is pending position assignment: retained arrival-order `pos=last+1` versus candidate `pos=event_seq`. SQLite `BEGIN IMMEDIATE`, content binding, consumer admission, ACK, capacity=2 and drain mechanics are shared.

## Allocation history

A1 (`fifo2-seqkey-20260917-a1`) was stopped by the external 45-second supervision ceiling after complete first outcomes m01..m08; m09 contains setup state but no result; m10..m12 never started. A1 was not resumed or pooled.

A2 changes supervision only: fresh n01..n12 IDs, one case per outer container invocation, identical scientific source/policies/order/gates. A1 pooled rows: 0; measured-ID reruns/replacements: 0.

## A2 first result

Frozen auditor: four strata ×3, errors `[]`.

- arrival-pos + seq-order: 3/3 pending `[E4,E5]`, both accepted, final `[E3,E4,E5]`.
- arrival-pos + reverse-order: 3/3 reproduces #731: pending `[E5,E4]`, E5 accepted then E4 `EVENT_NON_MONOTONIC`, final `[E3,E5]`, E4 remains pending.
- sequence-pos + seq-order: 3/3 pending `[E4,E5]`, both accepted, final `[E3,E4,E5]`.
- sequence-pos + reverse-order: **3/3** producer E5 transaction commits first, but stored order is `[E4,E5]`; E4 then E5 admit exactly once; final `[E3,E4,E5]`, pending empty.

Exact ACK replay remains `ACK_ALREADY_APPLIED` in all A2 cases.

## Integrity

Preformal remote readback matched frozen source identities. Static tests 3/3 PASS. Postformal source rehash has zero errors. Three copied-result corruptions plus one source corruption are rejected 4/4.

## Interpretation / boundary

For the already-observed case where both E4 and E5 are pending before drain, changing only the pending ordering key from transaction-arrival order to semantic `event_seq` closes the independent-producer inversion while preserving normal-order liveness.

This is not yet a complete sequence protocol. If E5 exists while E4 is absent, `sequence_pos` alone can still present E5 as head and the existing consumer would accept seq5 because it only requires monotonic increase, not contiguity. Missing-predecessor / contiguous-sequence admission remains the explicit next boundary. No distributed ordering, network reordering, power-loss, priority/fairness, throughput or production sizing claim follows.
