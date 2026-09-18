# Observation Epoch bounded-skew X11 R2 — retained result

Issue #1594. Parent #42. Direct predecessor #1580.

## Disposition

**PASS_OBSERVATION_EPOCH_BOUNDED_SKEW_X11_R2_SCOPED**

One source-frozen formal invocation, reruns0/replacements0/tuning0.

## Retained preformal stops

Two harness-only stops occurred before any scientific construction row:
1. `STOP_XAUTHORITY_MISSING`: python-xlib attempted the absent default Xauthority file. The repair used an explicit empty Xauthority with private `Xvfb -ac`.
2. `STOP_GETIMAGE_ARGUMENT_ORDER`: the harness passed X11 GetImage plane-mask/format arguments in the wrong order. The repair changed only that call signature.

Both are retained in `CONSTRUCTION_ATTEMPTS.json`. The fixed 2 ms budget and scientific gates were never changed.

## Construction

32 rows, eight per arm:
- stable/delayed-paint candidate joins: 16/16
- stale-focus candidate joins: 0/8
- naive timestamp-only stale-focus joins: 7/8
- identity-mismatch candidate joins: 0/8
- candidate/oracle mismatches: 0
- exact 16x16×4-byte image payload: 32/32
- focus restored after each row: 32/32

Construction, primary audit and implementation-independent raw-readback audit passed.

## Formal result

256 fresh private-X11 rows, 64 per arm:
- candidate/oracle mismatch: **0/256**
- candidate stale-focus joins: **0/64**
- candidate identity/generation mismatch joins: **0/64**
- valid stable + delayed-paint candidate joins: **128/128**
- naive timestamp-only stale-focus joins: **64/64**
- strict exact-anchor stable + paint joins: **0/128**
- stable + paint sample span within 2 ms: **126/128**
- stale-focus sample span within 2 ms: **64/64**
- terminal focus restored: **256/256**
- image payload exactly 1024 bytes: **256/256**

The longest total sample span was 3.424139 ms. This does not contradict the rule: the 2 ms budget applies only to explicitly noncritical image/UI-context age. Critical focus/geometry may be older only when final revalidation proves them valid through the newest anchor.

The primary audit passes four corruption controls. The independent auditor imports no experiment implementation; it derives row truth from retained initial/final X11 focus and geometry plus raw timestamps, and reports errors[] over all 256 rows.

## Interpretation

The synthetic R1 result transfers to this controlled X11 acquisition path. Timestamp closeness alone is unsafe: all 64 stale-focus rows remain inside the naive 2 ms timestamp discriminator and are falsely joinable by that rule. Revalidating critical fields through the newest anchor rejects all 64, while retaining all 128 stable/paint joins.

This is evidence for **temporal composition semantics**, not application readiness or task authority.

## Evidence limit

The 446,670-byte raw row result was hashed and independently audited locally. The current GitHub contents connector retains its cryptographic identity, summary and both audit outputs, but does not embed the raw row file itself. Therefore the branch preserves the formal decision and audited metrics but is not a standalone byte-for-byte reconstruction of every raw row.

## Scope / non-claims

- private same-host X11 only;
- 16x16 ROI, not full-screen capture;
- focus and target geometry only as critical fields;
- controlled fixture mutations;
- no model/token/task correctness/latency saving/human-tempo/general-GUI claim;
- no claim that 2 ms is a production threshold.

## Next legal rung

Keep the join rule unchanged and transfer it to an actual application delayed-paint/focus recovery path with capture intervals and explicit clock uncertainty. Do not change detector semantics and skew tolerance in the same allocation.
