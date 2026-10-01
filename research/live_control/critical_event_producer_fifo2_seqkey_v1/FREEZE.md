# Source-first freeze

Task: `CRITICAL-EVENT-PRODUCER-FIFO2-SEQKEY-20260917-004`
Issue: #742
Immutable BASE: `95bb57c4d651e5664fb5bbc7c79e50e852777f72`
Formal allocation: `fifo2-seqkey-20260917-a1`
Scope: `research/live_control/critical_event_producer_fifo2_seqkey_v1/**`

Formal measured cases before freeze: **0**. Construction uses only `c-*` IDs and is excluded.

Single factor: pending position assignment (`arrival_pos` vs `sequence_pos`). `BEGIN IMMEDIATE`, consumer semantics, ACK, capacity=2 and drain logic are shared. Formal: 12 fresh first outcomes = 3 reps × 2 position policies × 2 producer arrival orders. Rerun/replacement budget 0.

Missing-predecessor gap admission (for example E5 present while E4 absent) is explicitly out of scope and remains a successor boundary.
