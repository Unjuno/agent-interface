# Source-first freeze

Task: `CRITICAL-EVENT-PRODUCER-FIFO2-ORDER-20260917-003`
Issue: #731
Immutable BASE: `a4538c1edcaa8fb6a9305c303fa76c70561ffed9`
Formal allocation: `fifo2-producer-order-20260917-a1`
Scope: `research/live_control/critical_event_producer_fifo2_order_v1/**`

Formal measured cases before this freeze: **0**.
Construction uses only `c-*` IDs and is excluded.

Single factor: independent producer transaction arrival order. Every producer uses `BEGIN IMMEDIATE -> producer_offer(one event) -> COMMIT`, preserving the merged #717 transaction pattern. No sequence-aware repair is present.

Formal: 8 fresh first outcomes, four `seq_order_arrival`, four `reverse_arrival`, fixed `plan.json`, same-ID rerun/replacement budget 0.

Decision rule is Issue #731 / frozen `audit.py`. Exact file identities are in `source_hashes.json`.
