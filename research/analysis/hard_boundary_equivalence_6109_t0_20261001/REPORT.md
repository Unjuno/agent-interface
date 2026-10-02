# Issue #6109 T0 — scoped finite-method result

**Disposition: METHOD_PASS_SCOPED for the authored finite fixture only.** This is not GUI-route equivalence, safety evidence, empirical calibration, or production readiness.

## Question and scope

Can a quantitative route comparator accept a benign coordinate/timing perturbation while preserving hard semantic boundaries and all finite possible branches? The fixture uses 12 authored path-set cases, typed fields (`px`, `ms`, `score`), fixed independent cross-route referent maps, an injectivity check, and an explicit possible-divergence branch. Acyclic `tau` edges are hidden; divergence itself is never hidden. Every possible path must have a whole-path match in both directions. Task-predicate acceptance additionally requires each matched value's complete epsilon interval to remain strictly on one side of the threshold.

The route-local fresh-ID rename case passes only because both frozen maps point to the same referents; raw opaque IDs are not compared. Missing maps, distinct incarnations, non-injective receipt aliases, missing bounds, and unit mismatch HOLD. Soft tolerances are independent by field and are not summed. Effect-lineage, release, UNKNOWN, and stale-generation mutations are direct hard-label controls. The repeated-drift case is distinguished because its allowed envelope reaches/crosses the task boundary. The extra possible-divergence branch is distinguished.

## Results

The candidate produced the preregistered disposition in all 15 cases. A separately written auditor, which does not import candidate code and reconstructs whole continuations recursively, agreed on all 15. Construction controls passed 15/15 before freeze. The fixtures include one accepted non-exact case (`benign-jitter`), one accepted exact-semantic route-local-ID renaming (`renamed-fresh-ids`), one explicit possible-divergence mutation, target-incarnation/alias/generation/effect/release/UNKNOWN controls, one task-boundary crossing, and five HOLD controls.

This is self-authored finite-method evidence: the expected outcomes are fixture assertions, not an independent application oracle. Candidate and auditor share the public fixture and its stipulated assumptions. The small path-set algorithm is not a general weak-bisimulation implementation and does not model arbitrary state graphs, cycles, probabilistic behavior, hidden app state, unmatched input schedules, or liveness beyond the marked finite divergence branch.

## Execution and integrity

- Frozen base commit: `f590fde44595a70eb1752a4940fbc3f119b80a66`.
- Execution: host CPython, no network/model/GUI/application/GPU/physical-input calls. Docker CLI was present, but Docker Desktop Engine did not answer the bounded `docker info` probe; no shared backend restart was attempted. Thus **no container isolation is claimed**.
- The preliminary 12-case raw outputs are retained as `candidate.raw.json` and `audit.raw.json` and are superseded. After adding three missing hard-label controls, the 15-case corpus was separately frozen and candidate and auditor were each invoked once from this package directory; final raw outputs are `candidate.v2.raw.json` and `audit.v2.raw.json`.
- The pre-run comment on #6109 was incorporated before freeze: independent referent maps, injectivity, incarnation, lineage/freshness/order, and explicit possible divergence.
- No external route or model execution occurred.

## Research interpretation

The fixture supports only the narrow observation that the proposed finite policy separates its authored benign perturbation from its authored hard, branch, and boundary controls. It does not show that real route metrics can be calibrated, that hard referents can be independently established, or that this policy improves an agent. The source literature concerns specified metric transition systems and constrained linear systems; neither supplies a GUI metric or route oracle. Exact structural comparison plus separate interval robustness remains a simpler comparator worth evaluating on independently grounded traces.

## H/T/D/C/U

- **H:** Scoped fixture hypothesis met, including benign non-exact acceptance and preservation of hard/branch/task boundaries.
- **T:** 15-case finite authored fixture; candidate and independent continuation auditor; construction controls then one formal call each for the final freeze.
- **D:** `METHOD_PASS_SCOPED` for this fixture only; no integrated/production PASS.
- **C:** Exact typed bisimulation plus separate numeric margins may be simpler and equally discriminating.
- **U:** No empirical observation calibration, route coverage, independent app-effect truth, live authority, human-equivalence claim, or general cyclic/divergence semantics.
