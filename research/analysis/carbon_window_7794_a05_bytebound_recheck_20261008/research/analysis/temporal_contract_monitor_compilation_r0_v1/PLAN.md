# #1719 Bounded temporal-contract monitor compilation

TASK: `TEMPORAL-CONTRACT-MONITOR-COMPILATION-R0-20260918-001`

Parent #1661. This rung defines one-shot semantic monitors only.

## Canonical stream semantics

Input is a sequence of fragments with nondecreasing integer timestamps. Multiple fragments may share one timestamp. Same-time event labels are coalesced semantically: a monitor must not infer strict-before ordering merely from fragment arrival order.

A monitor therefore keeps the current timestamp open until a later timestamp arrives. This is required for cases such as C then D at the same timestamp: C is not strictly before D.

Descending timestamps are malformed and force UNKNOWN.

## Contract families

1. `A_THEN_B_WITHIN(delta)`: first A opens an obligation; repeated A does not restart it; B at A's timestamp or before/equal the closed deadline satisfies; advancing beyond the deadline without B expires.
2. `P_CONTINUOUS_FOR(tau)`: each fragment supplies current Boolean P; the final value at a timestamp persists until the next timestamp; false resets the run; satisfaction occurs when a true run spans at least tau.
3. `C_NOT_BEFORE_D`: C at timestamp t violates only once a later timestamp proves D did not occur at t. D at the same timestamp satisfies.
4. `AFTER_X_NO_Y_FOR(horizon)`: first X opens the horizon; Y at the same timestamp is not strictly after X; Y at a later timestamp through the closed horizon violates; advancing beyond the horizon without such Y satisfies.

Terminal outcomes are typed: PENDING, SATISFIED, VIOLATED, EXPIRED, UNKNOWN. PENDING is nonterminal; all others are terminal for one contract instance.

## H/T/D/C/U

H: each family is implementable with finite control plus current timestamp/co-timestamp buffer and at most one semantic anchor timestamp, independently of history length, and is exactly equivalent to explicit-history semantics.

T: exhaustive traces length0..5, timestamps0..4, all label combinations, parameters1..3 where applicable, candidate vs independently structured history oracle after every prefix; independent full re-enumeration; malformed-time and six semantic mutation controls.

D: PASS only with mismatch0, expected reachable outcome sets, fail-closed descending time, bounded state shape, exact independent count agreement, corruption6/6, formal1/reruns0/replacements0/tuning0.

C: missing observations, cross-clock ambiguity, hidden predicate transitions and overlapping repeated obligations violate this model.

U: semantic theorem only; no runtime timing/model/GUI/product claim.
