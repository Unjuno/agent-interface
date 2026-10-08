# Issue #7934 — one-step decision-value acquisition T0 A01

## H

On a finite, explicitly supported synthetic interface-state model, a one-step
decision-value rule will select a costlier, lower-entropy check when it reduces
the expected loss of the downstream safe-route decision, outperforming both
cheapest-check and entropy-threshold selection on two frozen disagreement
topologies at identical hard-gate correctness. It should buy no check when all
supported states prefer the same route, should not count a repeated correlated
observation twice, and should return `UNKNOWN` when checks are stale or the
model support is invalid.

This is a method hypothesis under stipulated weights, losses, signal models and
costs. It is not a claim about calibrated live beliefs or GUI utility.

## T0 design

The frozen model has six cases and 21 scored worlds:

1. `ig_conflict`: four equally weighted hidden states; a one-bit nuisance check
   does not change the route choice, while a lower-entropy decision check does.
2. `heldout_conflict`: an eight-state, three-to-two outcome topology reserved
   as a held-out structural confirmation, not used to alter the algorithm or
   thresholds.
3. `agreement`: all states prefer route A; observing cannot improve the route.
4. `correlated`: a prior nuisance observation is already known; an exact
   duplicate signal has zero conditional decision value.
5. `stale`: all available checks are stale, so the route remains UNKNOWN.
6. `unsupported`: the model declares its support invalid and the scoring key
   contains an outside-support world; every policy must abstain.

The four frozen arms are:

- `cost_only`: acquire the cheapest check costing at most 1.0.
- `entropy_threshold`: acquire the check with highest expected entropy
  reduction when it is at least 0.4 bits and costs at most 1.0.
- `decision_value`: acquire the check with greatest positive
  `current Bayes risk - expected post-check Bayes risk - check cost`.
- `oracle_best_check`: exact one-step exhaustive enumeration under the same
  declared model; a correctness reference for the selection computation, not
  an independent empirical policy.

All checks/routes in the supported cases are stipulated admissible. The
hard-gate measure is whether a policy emits an action outside the case's
declared safe route set; YIELD/UNKNOWN is permitted. Regret is realized
route-loss minus the best safe route's loss in the scoring-key world. Costs
are authored loss-equivalent units, not measured wall-clock latency.

## D

`PASS_METHOD_SCOPED` requires:

- exact independent reconstruction of all 84 policy/world rows;
- on both disagreement topologies, lower mean realized regret for
  `decision_value` than `entropy_threshold` at equal hard-gate correctness;
- no acquisition by `decision_value` on the agreement or zero-conditional-value
  duplicate-check cases;
- UNKNOWN/YIELD on stale or unsupported cases;
- zero hard-gate violations and zero authority grants;
- exact one-step oracle agreement and rejection of all six frozen raw/score
  mutation controls.

Any violated condition is `FAIL_AUDIT` or `FAIL_METHOD`; an input/source/runtime
identity mismatch is STOP before interpreting the policy results. No retry,
threshold tuning, or substitution of cases after the formal run.

## C

The exact enumerator may outperform baselines because the authored likelihood,
loss and cost model makes the downstream value identifiable. A simple fixed
route rule can dominate outside the two disagreement topologies. Fixture
construction may favor the proposed signal. The oracle is model-correct by
construction and does not validate calibration.

## U

Deterministic finite synthetic states only; no live GUI/tool outputs, measured
probabilities, nonstationarity beyond the explicit invalid-support control,
user data, model, OS action, physical effect, latency, task completion, safety
or product claim. No posterior may override hard authority, freshness or
admissibility gates. This tests one-step acquisition, not sequential
multi-check planning or empirical knowledge-gradient calibration.
