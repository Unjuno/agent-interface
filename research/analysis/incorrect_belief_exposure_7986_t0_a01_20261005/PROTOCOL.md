# Issue #7986 T0 A01 — action-conditioned incorrect-belief exposure

## H / T / D / C / U

**H.** In the frozen finite event-table fixture, unsafe-admissibility exposure distinguishes action-relevant belief error that observation age and effect-only summaries do not: an old but still correct belief has zero exposure, a stale belief after a state transition has positive exposure, and a freshly captured but misbound belief can have positive exposure despite low observation age. Exposure is zero outside live authority or an actual action opportunity. Realized unsafe effects remain a separate endpoint.

**T.** Eight deterministic one-interval rows: (1) old/correct; (2) stale after transition; (3) fresh/misbound; (4) wrong belief with no authority; (5) revoked/no action opportunity; (6) forbidden action actually emitted; (7) truth missing; (8) ambiguous clock order. Candidate-visible rows contain only belief/authority/action/effect observations. A disjoint truth sidecar supplies truth state, forbidden actions, and truth/clock certainty exclusively to the auditor. Compute observation age and age-at-effect separately from belief-error dwell, unsafe-admissibility exposure, and realized unsafe effects. One row represents a maximal homogeneous interval; no interpolation or interval joining.

**D.** `PASS_METHOD_SCOPED` only if the raw-only auditor reproduces the complete frozen result, including: row 1 zero belief-error/exposure despite observation age 10; row 2 six ticks of belief error/exposure; row 3 five ticks of belief error/exposure while observation age is one; rows 4–5 zero exposure; row 6 eight ticks of potential exposure and one separately counted unsafe effect at effect-age five; rows 7–8 report `UNKNOWN` (and ambiguous clock yields no numeric age); and frozen input/raw mutation controls fail closed. Missing/extra identifiers, hash mismatch, or any numeric discrepancy is FAIL.

**C.** Event-level contract violations, #6045 opportunity/lineage endpoints, or #5368 worst-case belief admission may already capture the operationally relevant information. A duration metric could add no predictive or decision value and merely relabel existing signals.

**U.** This is a tiny authored method fixture, not a deployed system. Ground truth is privileged and unavailable in ordinary use. No probability, harm, safety, human, live GUI, cross-application, policy, or runtime claim follows. Candidate and auditor were authored by one agent; their code separation is not independent human review.

## Frozen computation

All time is exact integer ticks and intervals are half-open `[start_tick, end_tick)`. For known truth and clock order, belief-error dwell is interval duration iff authority and belief are active and truth is excluded by the declared belief set. Unsafe-admissibility exposure is interval duration iff authority and belief are active, an action opportunity exists, and admitted actions intersect truth-forbidden actions. Realized effects count only in-interval emitted actions forbidden under truth. Unknown truth/order makes truth-dependent metrics `UNKNOWN`; ambiguous clock order also nulls numeric age. The candidate computes only observation and effect ages from its candidate-visible stream. The auditor independently reconstructs every age and truth-conditioned metric.
