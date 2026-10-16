# Finite sensorimotor graph: scroll/reveal semantics

Task `SENSORIMOTOR-GRAPH-REVEAL-20260917-001`, Issue #696.

**Decision: `PASS_SENSORIMOTOR_GRAPH_REVEAL_SCOPED`.**

A container-only matched study compared a separately expressed imperative scroll-until-visible controller with a six-node declarative sensorimotor graph. Both arms used the same current-pixel target predicate, CDP wheel adapter, freshness/action-generation checks, finite authority, budgets and effect scorer. No model/provider call was made.

Formal block: 8 scenarios × 2 representations × 3 repetitions = 48 fresh Chromium sessions / 24 matched pairs. Outcomes were 18 `VISIBLE` terminals and 30 expected typed stops (`ACTUATOR_BUDGET`, `UNKNOWN`, `STALE_SOURCE`, `CANCELLED`, `EXPIRED`). All 48 independent checks passed; all 24 pairs matched outcome, exact task-input count and final independently detected geometry.

The stale-source discriminator replayed the pre-action observation after one wheel. Both arms stopped `STALE_SOURCE` before a second wheel even though a later audit-only capture showed the target. Later valid pixels did not retroactively authorize the stale decision.

Static graph validation rejected 10/10 malformed controllers before backend access, including unbounded budget, out-of-subset actuator, missing cleanup, stale-only success, missing UNKNOWN disposition and missing post-actuation freshness. Nine copied-evidence corruptions were rejected 9/9. Forty-eight post-terminal continuations were refused with zero extra task input.

The source was locally SHA-256 frozen before formal execution (`FREEZE.json`); GitHub mutation was unavailable during measurement, so this publication is explicitly **post-measurement** and is not represented as a GitHub preregistration.

Scope: synthetic exact-color browser fixture, wheel-only task input, no held-key/contact crash recovery, no measured native focus-loss path, no planner/token/speed claim. This establishes a scoped equivalence/static-audit result, not a general graph language or production runtime integration.

Next question: transfer the minimal graph to an ordinary application with a verifiable focus-interruption source before expanding the node vocabulary.
