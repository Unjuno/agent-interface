# Independent producer arrival order versus FIFO2 event sequence — retained result

Task `CRITICAL-EVENT-PRODUCER-FIFO2-ORDER-20260917-003`, Issue #731. Immutable publication BASE `a4538c1edcaa8fb6a9305c303fa76c70561ffed9`.

## Decision

**`RETAIN_FIFO2_PRODUCER_ORDER_BOUNDARY_SCOPED`.**

The exact merged #717 `model.py` is reused byte-for-byte (Git blob `84279711dfb47299aa92a8ed8a2f39ee6c3277ff`). Each independent producer uses the retained transaction shape `BEGIN IMMEDIATE -> producer_offer(one event) -> COMMIT`. The only scientific factor is transaction arrival order for E4/seq4 and E5/seq5.

## First outcome

Eight fresh first cases, four per arm; formal reruns/replacements zero.

- `seq_order_arrival` 4/4: E4 commits before E5, pending is exactly `[E4,E5]`; after ACK-through-E2 and exact ACK replay, E4 then E5 each return `EVENT_ACCEPTED`; final consumer `[E3,E4,E5]`, pending empty.
- `reverse_arrival` 4/4: E5 commits before E4, pending is exactly `[E5,E4]`; after capacity opens, E5 returns `EVENT_ACCEPTED`, then E4 returns `EVENT_NON_MONOTONIC`; final consumer `[E3,E5]`, pending `[E4]`.
- ACK exact replay is `ACK_ALREADY_APPLIED` in every case.
- Frozen auditor: counts 4/4, errors `[]`.

The result separates **mutual exclusion** from **semantic event ordering**. SQLite `BEGIN IMMEDIATE` correctly serializes independent producer writes, but the retained positional FIFO orders by producer transaction arrival, not `event_seq`. A later-sequence event can therefore become head first and make the earlier event permanently non-monotonic after drain begins.

## Integrity

Preformal source/readback identities match; `model.py` exactly matches #717. Static tests 2/2 PASS. Postformal source rehash reports zero errors. Three copied aggregate corruptions and one source-hash corruption are rejected 4/4.

The outer container-tool invocation returned a 45-second timeout only after all eight `result.json` files, `aggregate.json`, and the frozen `audit.json` were present. No measured ID was rerun. `SUPERVISION.json` retains this output/supervision incident separately from the scientific result.

## Boundary

This is a controlled same-session independent-producer arrival-order fixture, not a natural race-rate estimate. It does not show that `BEGIN IMMEDIATE` is unsafe; it shows that serialization does not define semantic sequence order. No sequence-aware owner/buffer repair is tested here. No distributed producers, network reordering, priority/fairness, power loss, throughput or production sizing claim follows.
