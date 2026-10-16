# #2802 simultaneous-obligation keying rung

Allocation: `app-obligation-keying-2802-20260923-01`.

## Analytical reduction
If one monitor ignores obligation identity, the trace `A(o1), B(o2)` is indistinguishable from a valid A→B trace at label level. Therefore a shared unkeyed state can cross-satisfy obligations. The empirical residual is whether a real subprocess event stream preserves obligation IDs, sequence and a shared logical application tick, and whether a per-obligation candidate matches the independently observed target effect at every prefix.

## H
For target obligation o1, only events explicitly bound to o1 may advance its temporal monitor. Events for o2 at the same source/tick must not satisfy o1. Missing obligation identity must yield UNKNOWN_ID. Per-obligation prefix state should match the target's actual private effect; a shared-label comparator should expose false prefix success.

## T
Six scenarios × three cyclic repetitions =18 fresh application child processes over actual stdout pipes. Every event carries source_id=app, clock_domain=APP_LOGICAL_TICK, one shared logical tick per case, increasing seq, obligation_id, label and host monotonic arrival_ns. The child updates a private scoring-only {o1,o2} state before each matching B. Target is always o1. One formal invocation, no retry/replacement/tuning.

## D
`PASS_OBLIGATION_KEYING_BOUNDARY_SCOPED` iff all18 rows/exits/provenance/effects complete; candidate terminal and every prefix match independent oracle; candidate results are BOTH_COMPLETE SATISFIED3, CROSS_ONLY PENDING3, WRONG_B_THEN_RIGHT SATISFIED3 only at the final o1 B, O2_COMPLETE_ONLY PENDING3, INTERLEAVED_COMPLETE SATISFIED3 only at the final o1 B, MISSING_ID UNKNOWN_ID3; unsafe shared comparator has at least one false-o1 prefix in all15 cases from the five discriminator scenarios; 12/12 evidence corruptions reject; frozen source hashes unchanged.

## C
Logical tick is application-authored metadata, not a physical clock or causality proof. One trusted producer process and one target obligation are scored. The unsafe comparator is a deliberate control, not an upstream implementation allegation.

## U
Multiple producers, ID forgery, dropped transport bytes, reconnect, obligation cancellation/reuse, cross-process distributed clocks, GUI/model/task benefit, input authority, reliability and production integration remain open.
