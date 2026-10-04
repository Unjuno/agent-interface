# Issue #7808 — vector-constraint approachability T0

## Status and scope

New one-shot synthetic method allocation `VCA-7808-WSLC-A01-20261005`, based on current main `aa2e4b623b2f4ccdcbc8e294535bab09c0092f30`. This tests a finite policy comparison only. It grants no runtime authority and makes no empirical route-benefit or user/product claim.

## H / T / D / C / U

**H.** In the frozen alternating-context feasible case, the vector-debt selector will keep both average soft costs within the convex upper-bound target and produce more independently verified useful effects than the fixed-scalar and independent threshold/freeze comparators, without any hard-gate violation. It will report an infeasible target as not converged and incomplete feedback as unknown.

**T.** A standard-library finite game uses three already eligible routes per opportunity, two soft metrics (model-boundary count and elapsed-cost units), two revealed contexts, an independently scored binary useful-effect outcome, and a rectangular convex target set. Arms are: (1) Blackwell-style steering using the positive vector debt above the target and current context forecasts; (2) fixed equal-weight scalar cost; (3) independent per-metric threshold/freeze, which activates only axes with positive accumulated debt, keeps choices at or below the target on all pressured axes where possible, then chooses minimum total predicted cost (ties by utility and route name); (4) an exhaustive offline feasibility/oracle search over the finite eligible route sequences. The frozen input includes four cases: feasible alternating tradeoff, infeasible target, delayed plus permanently missing feedback, and a single realized extreme episode that differs from its forecast. The learner sees current context forecasts, prior delivered feedback, and eligibility; the independent scorer returns only the chosen route's result. It never uses a missing outcome as zero. A separate tuple/ID based auditor recomputes all route decisions, histories, means, maximum per-episode cost, feedback deliveries, target status, hard-gate outcomes, and exact oracle feasibility/utility. Four mutation controls test zero-imputation of missing feedback, hard-gate bypass, a false convergence claim on the infeasible case, and relabeling an attempted/no-effect action as verified success. No GUI, model, user data, network, GPU or external effect.

**D.** `PASS_METHOD_SCOPED` if the auditor matches all candidate traces; the vector selector meets both feasible-case targets and exceeds both online baselines in verified useful effects; the offline oracle independently confirms feasibility; the infeasible case has no feasible sequence and no convergence claim; delayed/missing feedback remains explicitly incomplete/UNKNOWN; the extreme episode remains visible in maximum cost reporting; every hard gate passes; and all four mutations are rejected. `FAIL_METHOD` for any mismatch, hidden missingness, average-only masking of the extreme, unsafe choice, or false success/convergence. `UNCERTAIN_NO_RESIDUAL` if the approachability arm is equivalent to or worse than the independent freeze comparator on useful verified effects while both meet the same target. Candidate and auditor execute once each after freeze; zero retries. Construction tests use separate in-memory/temp outputs and do not count as the frozen candidate/audit allocation.

**C.** A fixed scalar route score can suffice when weights are explicit. Independent freeze rules may meet the target with less complexity. Route outcomes may be heterogeneous and context predictions may be wrong; a finite context sequence can favor a selected policy.

**U.** Authored deterministic forecasts/outcomes, short finite horizon, binary synthetic effect oracle, and exact context knowledge are idealized. The experiment tests method bookkeeping and one declared sequence only; it does not show real trace availability, causal benefit, safety, deadlines, latency, or user preference.

## Expected value / cost / risk

If a discriminating result and an eligible real trace class exist, this gives #57 a principled alternative to arbitrary scalar cost weights for balancing non-safety efficiency constraints under changing conditions. It may also show the approach is redundant or unsuitable, preventing over-engineering. T0 is low-cost deterministic enumeration; empirical transfer requires complete task-level outcome provenance and matched opportunity definitions. Main risks are metric gaming, false confidence from average bounds, and allowing a soft performance controller to blur hard authority/safety invariants.

## Construction history before freeze

- The first host construction run was stopped after repeated uncached exhaustive-oracle work exceeded the bounded construction window; no formal outputs were written.
- After adding a per-fixture oracle cache, the host suite initially reported 4/5. The sole failure was an incorrect test expectation (`6`) for the explicitly frozen minimum-total-cost comparator; exact trace inspection showed 0 useful effects. The assertion was corrected before freeze.
- The final host suite passed 5/5, and the same 5/5 construction suite passed under the pinned WSLc image. These are construction checks, not formal candidate/auditor invocations.

## Execution and custody

WSLc 3.0.1.0; pinned cached image `python:3.12-slim@sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016`; stdlib only. Run construction tests before freeze. Then hash `fixture.json`, `candidate.py`, `audit.py`, `test_protocol.py`, and this plan. Formal outputs must be absent before exactly one candidate and one auditor invocation. Run with `--pull never --network none --cpus 1 --memory 128m --rm`; retain any WSLc cgroup/swap enforcement warning and do not infer configured memory as verified. No retry. Package path: `research/analysis/vector_constraint_approachability_7808_a01_20261005/`.

