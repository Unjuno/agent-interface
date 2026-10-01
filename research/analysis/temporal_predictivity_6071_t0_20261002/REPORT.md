# Issue #6071 T0 — scoped schedule-coherence result

**Disposition: METHOD_PASS_SCOPED for the frozen schedule table only.** No participants, human timing, comprehension, or GUI-agent benefit were measured.

## Results

Across 16 fixed task vignettes (8 `READY_TO_REVIEW`, 8 `NEEDS_HUMAN_DECISION`), all three arms have mean delay 5,000 ms. A is constant (variance 0); B and C have the identical 2,000/8,000 ms multiset (8 each; variance 9,000,000 ms²). In B, each response type receives four short and four long delays, giving empirical mutual information 0 bits. In C, type maps deterministically to delay, giving 1 bit. Result-content references and machine-effect truth are shared by task identity across arms; there are no arm-specific result/authority/deadline fields. Arm order and forward/reverse task orders are balanced. The safety contract contains no emergency alert, deadline, authority change, live action, or timing-encoded correctness.

The candidate raw and independent auditor raw agree on every candidate summary field. The auditor additionally emits a top-level B-by-type delay-count table, which exactly matches the candidate's nested B type-count table. A strict whole-object equality assertion initially failed only because of that additional auditor field; the preserved raw outputs were then reconciled by shared-field projection and the extra count was directly compared. This schema-only postprocessing correction is recorded rather than hidden. It does not change the schedule values or conclusion.

## Interpretation and limits

This shows only that the proposed no-participant schedule can hold the marginal delay distribution, mean, task content/effect truth and response-type counts constant while making one variable timing arm uninformative and the other perfectly informative about the next response category. The synthetic 1-bit relation is a design property, not evidence that people notice or use it. It also does not justify intentionally delaying ready results. A future human study would need separate governance, consent, accessibility and safety review, actual measured delay fidelity, objective next-action onset, independent correctness and full assignment-to-resolution time. Perceived thoughtfulness is not a substitute for those endpoints.

## Execution and integrity

- Frozen source base: `3adec9cdc2cff5ef68f19acd55c5823fcaad26df`.
- Candidate and independent auditor each invoked once after the output-absence check; both exited 0. Raw stdout retained and SHA-256 pinned in `RUN.json`/`SHA256SUMS`.
- Pre-freeze construction checks passed, including timing/type leakage, arm-specific-content, safety-contract and marginal-delay corruption controls.
- Host CPython only. Docker Engine was unavailable; no shared backend restart or container-isolation claim. No people, user data, model/provider, network experiment, GUI, app, game, GPU or physical input.

## H/T/D/C/U

- **H:** Matched-distribution schedule contrast and invariants achieved in the finite design.
- **T:** 16 paired synthetic vignettes, A/B/C schedules, exact counts and mutual information, arm/task-order counterbalance, independent raw reconstruction.
- **D:** `METHOD_PASS_SCOPED` for schedule construction only; not an HCI effect.
- **C:** Explicit truthful status labels may help more than timing; A/B/C cannot establish which presentation improves human work.
- **U:** No actual timing execution, participant response, accessibility test, population inference, or agent integration.
