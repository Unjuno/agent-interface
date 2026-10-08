# A02 pre-run freeze — Issue #8640
Status: methods-only analytical allocation; no result claimed yet.
Source base: main `99f2521811df790db3c96cdfa9313a6296f247f7`.
Branch: `research/8640-ascertainment-a02-20261008`.
Path: `research/analysis/policy_ascertainment_8640_a02_20261008/`.

## H / T / D / C / U

H: On a finite known task population, policy-dependent observation/censoring can reverse resolved-only route ranking. Exact inverse-probability weighting recovers the finite route means only where every route-unit has a correct, logged, positive inclusion probability; assumption-free bounds retain truth but may not identify a winner when positivity fails.

T: Exhaustively enumerate two blocked-randomized route assignments and all 16 ascertainment masks for each of five frozen four-unit scenarios: invariant ascertainment, logged route-dependent ascertainment, fixed-horizon censoring, a zero-probability stratum, and a misspecified/hidden selection probability. Compute true potential-outcome means, resolved-only rates, logged-propensity IPW estimates where identifiable, finite-population bounds, and rank-reversal probability. A separate raw-only auditor verifies all assignments/masks, exact per-world probabilities and metrics, bound coverage, expectation summaries, and corrupted-record rejection.

D: PASS_METHOD_SCOPED only if the complete-ascertainment control has no ranking reversal; at least one positive-propensity selected-label case has a reversal while its expected logged-IPW estimate matches truth; zero positivity and hidden/misspecified propensity do not receive a valid identified IPW claim; all finite-population bounds contain truth; and all five frozen corruptions are rejected by the independent auditor. Otherwise FAIL or HOLD, with no historical/live inference.

C: The mechanism is absent when independent ascertainment is complete and policy-invariant. Under positivity/ignorability failure, inverse weighting cannot identify the population result; complete outcome accounting or assumption-free bounds are required.

U: Four-unit synthetic population, fixed binary outcomes, exact probabilities, no stochastic runtime or GUI. This demonstrates arithmetic/identification only, not bias in historical repository results, causal benefit of any route, or suitability of a production estimator. No safety gate is weighted or weakened.

## Frozen fixture and execution limits

The candidate source and exact fixture are committed before execution. Assignment is independently randomized within each of two pairs, one unit per pair to each route (probability 1/2). The target population contains four units. Horizon is 3. All 4 assignments × 16 observation masks are represented per scenario, including zero-probability masks. Exact enumeration only; no random seed, model, GUI, external service, network, Docker, WSLC, shared resource, or host-side container is used. Raw output, auditor output, command/runtime, hashes and limits will be appended only after their respective execution. A previous distinct attempt A01 stopped at the local output write with ENOSPC; it is not rerun or reclassified.
