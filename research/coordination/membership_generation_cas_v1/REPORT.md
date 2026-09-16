# Membership-to-generation CAS result

Task: `COORD-MEMBERSHIP-GENERATION-CAS-20260916-015`

Decision: **`PASS_CANONICAL_MEMBERSHIP_GENERATION_CAS_SCOPED`**

## Question

Does a membership change between final membership/confirmation validation and a separate generation commit create a cross-file TOCTOU, and can one canonical GitHub content-CAS record containing membership identity plus active generation close that specific window?

## First outcome

| Case | Intervening change | Generation commit | Final state |
|---|---|---|---|
| split race | membership epoch1 `{A,B}` -> epoch2 `{A,B,C}` | separate coordination write **succeeded** | membership epoch2 `{A,B,C}`, generation 2 |
| canonical race | canonical epoch1 `{A,B}`/g1 -> epoch2 `{A,B,C}`/g1 | old-validation-SHA write **HTTP 409** | epoch2 `{A,B,C}`/g1 |
| canonical stable | none | canonical SHA-CAS write succeeded | epoch1 `{A,B}`/g2 |

The split-file negative control therefore retained a stale advance: membership changed after `ALL_CONFIRMED`, but the independent coordination file still had the old unchanged SHA and accepted the generation update.

In the canonical race, final validation was bound to canonical blob `6b0b41a9c9ce6bba3c676ba5321e807a7d5004e1`. The membership change updated that same path. The later generation payload derived from the old validation reused the stale blob SHA and GitHub rejected it with HTTP 409. One readback showed epoch2 `{A,B,C}`/g1. The policy returned `HOLD_MEMBERSHIP_CHANGED`; there was no fresh-SHA retry.

The stable canonical control advanced to g2 once, so the candidate does not merely block all transitions.

## Retained measured commits

- split membership change: `15ed640defa431636690e7e489284ec39b54c823`
- split stale generation advance: `f0d48cd7b19b1efc1a6365576c10deb059a45459`
- canonical membership change: `10b7f2ef6af8757b1703b447dab1653d2fec059a`
- canonical stable advance: `4b36eaf8007e64c63d828df07f0f781f0001c5a4`

Canonical stale generation attempts: 1. GitHub stale-SHA 409s: 1. Post-409 GETs: 1. Fresh-SHA retries: 0.

## Interpretation

Binding membership identity and generation to the same content-CAS object turns a membership change into a failed stale generation commit in this fixture. A separate membership file plus coordination file cannot provide that property merely by validating both before the write.

This is the same general principle already observed for claim registers: a semantic validation is only protected against later mutation when the eventual write is conditionally bound to the exact state that was validated.

## Boundary

This is sequential GitHub-backed evidence. It does not establish simultaneous-request linearizability, distributed consensus, membership-change authorization, crash recovery, or production throughput. A single canonical path also creates more contention between membership and generation updates.

Critically, the confirmation batch remains a separate durable record. This rung closes the membership-to-generation race only. If confirmations can be revoked/replaced after validation while the canonical membership/generation record remains unchanged, the same stale decision class can still exist across the confirmation/canonical boundary.

## Next single question

Keep the canonical membership+generation CAS fixed. Change only the confirmation record after final validation and before the canonical generation commit. First demonstrate whether the generation commit still succeeds from a stale confirmation decision. Then test the smallest binding mechanism: place the exact confirmation digest/revision (or a one-use transition token derived from it) in the canonical CAS precondition so a changed confirmation cannot authorize the old transition.

Do not add quorum thresholds, timeout eviction, or membership authorization in the same rung.
