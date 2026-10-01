# Preregistration: T2 metric-guided selection feedback

Issue: #5686, prospective T2 extension; T0's result remains unchanged.

## H / T / D / C / U

- **H:** On a frozen target population, choosing a policy by its intermediate metric can select an authored candidate that appears fast on selection observations but loses endpoint utility or observation coverage on a disjoint sealed population; non-compensable safety must reject even a high-utility metric winner. A separate finite selection-overfit control should yield HOLD rather than being attributed to policy-induced population shift.
- **T:** Enumerate a fixed menu of three policies in each of four authored worlds, over four predeclared strata and two replicates in each of disjoint `selection` and `sealed` splits. Retain all attempts and missing observations. Independently choose (A) minimum observed intermediate latency and (B) maximum complete, safety-qualified selection-set endpoint utility; evaluate both selected policies on the same sealed opportunities. Raw-only audit reconstructs every row, split, selector, sealed score, safety count, and disposition. Corruption controls drop an attempt, change stratum/split, and substitute bool for integer.
- **D:** `PASS_SELECTION_FEEDBACK_GATE_SCOPED` iff all 192 expected attempts and four summaries are present, selection/sealed IDs are disjoint and complete, independent recomputation agrees, the stable world is scoped concordance, the selection-overfit world is HOLD without endpoint gain, the observation-shift world is rejected for coverage/endpoint regression, and the unsafe metric winner is rejected non-compensably. Any dropped/changed/relabelled row or unknown record type fails the audit.
- **C:** The worlds are deterministic authored controls, not a stochastic estimate. A selected-set/sealed-set mismatch can reflect ordinary selection overfit; only the separate coverage-shift control encodes policy-dependent observation availability. Endpoint utility is a finite scalar and does not represent a universal task value.
- **U:** This experiment does not show that a real interface changes its task mix, that any existing metric is performative, or that a real policy should be selected. No empirical task/model/GUI data, causal effect, or transport validity is established. Small finite concordance is not surrogate validation.

## Frozen design details

Predecessor allocation `SURROGATE-SELECTION-5686-T2-GHA-20261001-01` ran the candidate container successfully (exit 0; candidate artifact retained) but the auditor container was not launched because the workflow resolved the downloaded artifact under an incorrect extra directory. It is terminal, `NOT_EVALUATED`, and will not be retried; see Actions run https://github.com/Unjuno/agent-interface/actions/runs/36809600904 and raw artifacts under `raw/formal/allocation-01/`.

Successor allocation: `SURROGATE-SELECTION-5686-T2-GHA-20261001-02`.
Distinct branch: `research/surrogate-selection-feedback-5686-t2-a02-20261001`.
Frozen base main: `5ff239141f49c1603c0f6b078268f4a2f6e082df`.
Only operational correction: use the actual download-artifact layout `candidate-input/candidate-evidence/candidate.jsonl`. Fixture, candidate, independent audit, expected dispositions and D remain unchanged. The candidate is run once in this new allocation and the auditor runs once only after reading its exact JSONL. No retry or source mutation after dispatch.

The four authored worlds and expected dispositions are:

1. `stable` → `SCOPED_SELECTION_CONCORDANCE`.
2. `selection_overfit` → `HOLD_METRIC_SELECTION_EFFECT_NOT_REPLICATED`.
3. `observation_shift` → `REJECT_SELECTION_COVERAGE_OR_ENDPOINT_REGRESSION`.
4. `safety_regression` → `REJECT_NONCOMPENSABLE_SAFETY_REGRESSION`.

The metric winner is selected only from the selection split using observed latency, with policy ID as deterministic tie-break. The endpoint selector excludes incomplete or unsafe policies, then maximizes mean endpoint utility, with the same tie-break. Sealed evaluation uses the original equal-weight target opportunity inventory; missing endpoint outcomes count as zero for the registered utility summary and are separately counted as incomplete. A hard-safety event always rejects regardless of utility.

This allocation runs once on its first branch-creation push in two separate bounded, network-disabled Docker jobs using the previously verified pinned Python image. No push or same-allocation retry is allowed after dispatch. A STOP/runtime error is retained as non-scientific `NOT_EVALUATED`; a candidate exit failure skips the auditor. Formal raw outputs and independent audit will be recorded additively without changing this preregistration.
