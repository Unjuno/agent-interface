# Issue #6129 T0-02 — typed endpoints, recovery, switching and attribution

## H/T/D/C/U

- **H:** A pending-aware as-of route card preserves all assigned attempts and typed terminal events, treats YIELD as intermediate, reports UNKNOWN under unidentified censoring or cross-task state coupling, and avoids declaring a task-effect gain when switching work grows.
- **T:** One frozen seven-case finite fixture, checkpoint 1 and deadline 3. Includes exact delay inversion, equal-delay null, known-independent administrative follow-up loss, safe stop versus wrong effect, YIELD then later success, outcome-dependent/unknown loss, and state-coupled cross-task effects. Route-switch charge has four separately named components.
- **D:** `PASS_METHOD_SCOPED` only if all seven predeclared decisions and exact checkpoint bounds/counts reconstruct, typed outcomes remain distinct, YIELD stays pending at checkpoint (without future leakage), route-switch charges are exact, state-coupled and unknown-censor cases are UNKNOWN, and both mutation controls fail closed.
- **C:** Authored finite CPU fixture, exact rational bounds, no live routes, no model calls, no user data. Candidate sees only checkpoint-visible events and `visible.json`; independent audit separately reads truth. One candidate and one auditor invocation each in pinned, network-disabled OrbStack containers.
- **U:** No empirical route benefit, policy stability, causal claim, production routing, or imported delayed-bandit guarantee. Declared-independent censoring is a fixture assumption, not an empirical test of MCAR. The finite state-coupled case only demonstrates a model-mismatch boundary.

## Estimands and accounting

Primary endpoint: verified success by the declared deadline among all assigned attempts, with `VERIFIED_FAILURE`, `VERIFIED_WRONG_EFFECT`, `POLICY_TERMINAL_SAFE_STOP`, administrative loss, unresolved pending, and intermediate YIELD separately reported. Safe stop and wrong effect are not collapsed into generic failure or censoring. At checkpoint 1, no event after that time is candidate-visible; future terminal labels reside only in `truth.json` for audit.

Switching cost is separately charged as re-observation 2 + handback 3 + release 1 + revalidation 4 = 10 work units per route change. Fixed `A,A,A` costs 12 base work units; switching `A,B,A` incurs two changes and 32 total work units. This is an authored accounting control, not a measured runtime cost.

When attribution is state-coupled, route-arm comparisons are `MODEL_MISMATCH_UNKNOWN` unless matched episode identification is available. When loss mechanism is unknown/outcome-dependent, no route ranking is issued.
