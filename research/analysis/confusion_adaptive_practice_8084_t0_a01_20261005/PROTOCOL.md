# Issue #8084 — T0 method-readiness allocation A01

## H / T / D / C / U

**H.** In this finite authored design, a pre-outcome heterogeneity gate can activate learner-specific pair-focused interleaving only when the supplied confusion matrix clears the fixed span and peak thresholds; otherwise adaptive ordering falls back exactly to the equal-exposure neutral schedule. Independent scoring must reject wrong-target, false-success and outside-family traces.

**T.** Freeze six synthetic confusion matrices (three high-heterogeneity pair patterns, one uniform negative control, one low-dispersion control, and one above-threshold boundary), three practice variants, three separately held-out variants, four attempts per practice variant, and a maximum identical run of two. Compare a deterministic seeded neutral schedule with a dynamic-programmed pair-targeted schedule. The adaptive scheduler receives only the practice variants and matrix; held-out IDs and effect truth are in a separate scorer-side fixture. An independently implemented auditor reconstructs threshold decisions, optimal pair/order, equal exposure, streak bounds, held-out exclusion and exact effect-oracle labels. Include mutations for held-out leakage, missing exposure, forged eligibility, and false effect. No participant, human data, model, GUI, runtime, or authority.

**D.** `METHOD_PASS_SCOPED` only if every schedule and scorer row is independently reconstructed; per-variant exposure is exactly equal across arms; the adaptive schedule maximizes adjacency of the predeclared highest-confusion pair among schedules satisfying exposure and run caps; uniform/ineligible cases are exact neutral fallbacks; held-out variants are never in practice; and all mutations are rejected. Any discrepancy is `HOLD_METHOD_GATE`/`FAIL_METHOD`; no human-effect decision is possible at T0.

**C.** The synthetic generator makes the highest-confusion pair known and the schedule optimizer can exploit that signal by construction. It does not show that human confusion estimates are reliable, the heterogeneity thresholds are useful, or adaptive ordering improves learning; seeded neutral schedules may themselves contain target-pair adjacency.

**U.** This is schedule/scorer method readiness only. No participant learning, retention, transfer, safety, accessibility, burden, or GUI result is measured. T1 needs separate consent/privacy/ethics review, preregistration, and explicit coordination with #8080; this allocation does not grant those.

## Frozen parameters

`cases.json` has six matrices with `pair_order=[AB, AC, BC]`, `minimum_span=0.25`, and `minimum_peak=0.70`. Exactly `4×3=12` practice slots are used in each arm. Pair-targeted schedules use deterministic lexical tie-breaking over exact maximizing schedules. A held-out ID is never passed to the candidate process. The independent effect oracle is `scoring_cases.json`.

