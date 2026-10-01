# Observation Epoch bounded-skew R1 — retained result

Issue #1580; parent #42; predecessor #1218 strict-join semantics.

## Disposition

**PASS_OBSERVATION_EPOCH_BOUNDED_SKEW_R1_SCOPED**

One frozen formal invocation. Reruns0 / replacements0 / tuning0.

## Analytical conclusion

Small timestamp distance is not enough to compose consequential observations. A critical field can be sampled immediately before a state change and a newer image immediately after it while both timestamps remain inside a nominal skew budget.

The retained candidate anchors the join at the newest sample completion. Session, surface and currentness generation must match. Critical fields must remain explicitly valid through that anchor. Only noncritical fields may be older than the anchor, and only within the frozen bounded-skew budget.

This is a temporal composition rule, not semantic readiness or action authority.

## Formal result

300,000 deterministic rows, seed `4220260918001`, six classes of exactly 50,000 rows each.

- candidate/oracle mismatch: **0**
- candidate stale-critical joins: **0**
- candidate cross identity/generation joins: **0**
- candidate malformed/missing/future joins: **0**
- valid candidate joins: **100,000**
- valid candidate joins rejected by strict exact-anchor comparator: **50,000**
- naive pairwise-skew stale-critical joins: **50,000**
- critical-expiry rows: **50,000**
- identity/generation mismatch rows: **100,000**
- malformed/missing/future rows: **50,000**

Directed counterexamples also pass:
- focus expires inside the skew window: candidate/oracle reject, naive pairwise-skew accepts;
- valid staggered noncritical evidence: candidate/oracle accept, strict exact-anchor rejects.

Primary audit passes with six corruption controls. Independent audit does not import candidate/oracle/runner; it verifies the frozen closed-form category counts and disposition.

## Scope

This establishes a scoped semantic requirement for a future `BOUNDED_SKEW(delta)` observation epoch:
1. a shared identity/currentness generation is mandatory;
2. critical-field validity must cover the selected anchor;
3. bounded temporal slack belongs to explicitly noncritical evidence.

It does **not** establish a production delta, GUI correctness, model benefit, token savings, latency reduction, application readiness or human-tempo control.

## Next legal rung

Transfer the unchanged join semantics to one controlled delayed-paint/focus fixture. Change only acquisition timing/field observations; do not retune the skew rule and detector semantics together. Retain strict joining as the safety/value comparator and the naive timestamp-only rule as the negative discriminator.
