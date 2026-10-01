# Content-bound idempotent ACK replay — formal result

Task `CRITICAL-EVENT-ACK-REPLAY-20260917-001`, Issue #680.

## Decision

**`PASS_CONTENT_BOUND_ACK_REPLAY_SCOPED`**.

This is the one-variable successor to #668. Event admission/backpressure, capacity=3, per-session ordering and latest-state separation remain fixed. Only duplicate/lost-response ACK semantics differ.

## Formal discriminator

The frozen 14-row matrix ran exactly once. Initial ACK-through-E1 behaves identically in both policies: E1 is removed and the event queue becomes `[2,3]`.

After simulating a lost ACK response and retrying the exact same `(session=A, through_seq=1, acknowledged-prefix digest)`:

- strict baseline: `ACK_APPLIED -> ACK_NON_MONOTONIC`; queue remains `[2,3]`, but the retry response does not positively identify that the original ACK committed.
- candidate: `ACK_APPLIED -> ACK_ALREADY_APPLIED`; the retry is explicitly idempotent and its before/after full-state digests are identical.

After appending E4, exact retry of the old latest ACK remains `ACK_ALREADY_APPLIED` and leaves `[2,3,4]` untouched. Same `through_seq=1` with a changed digest becomes `ACK_RECEIPT_CONFLICT` with zero mutation. A later valid ACK-through-E2 applies normally, leaves `[3,4]`, and replaces the bounded latest receipt with the E2 receipt.

Cross-session control preserves session B's state/event while retrying session A. Unknown session, future ACK, malformed digest and non-monotonic record input fail closed.

## State bound

The candidate retains **one latest ACK receipt per session**, `(through_seq, acknowledged_prefix_sha256)`. It does not add an unbounded ACK history. Exact replay support is therefore intentionally limited to the latest committed ACK.

## Integrity

Construction was excluded. Before freeze: 5/5 unit tests PASS, 9/9 evidence corruptions rejected. Source bundle and FREEZE were remotely byte-verified before formal execution.

Formal SHA-256 `4879b5d4facba952e0dbb0b6554420d711c1e0e33930a816b37057339814b255`. Frozen audit passes with zero errors. Postformal source hashes match the freeze, frozen tests re-pass, and 9 direct mutations of the actual formal result are rejected.

## Boundary

This does not make ACK transport durable. It shows only that **if the consumer committed the latest ACK but its response was lost**, an exact content/sequence-bound retry can confirm that commit without deleting additional events. The receipt is not peer authentication. Older ACK replay after a later ACK has advanced is outside this rung. Producer persistence across `EVENT_BACKPRESSURE`, crash/fsync semantics, distributed delivery, latency and production queue sizing remain unresolved.

Next discriminator: keep these consumer semantics fixed and test **producer-side retention/retry of the overflowing event across `EVENT_BACKPRESSURE` plus lost ACK response**.
