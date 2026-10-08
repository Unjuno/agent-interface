# Frozen T0 protocol — Issue #6001 hidden behavior shifts

This is an offline deterministic mock-service experiment. No provider, model, remote API, GUI or live allocation is used. The candidate sees only `candidate_observations` and the canary responses it requests; `evaluator_truth` is audit-only and must not influence the policy.

## Hypothesis and contrast

Under a stable model alias and unavailable snapshot identity, a task-relevant behavior change detectable by the fixed canary deck should cause the bracketed-canary policy to hold a route comparison, whereas alias-only and exposed-metadata-only policies cannot detect that hidden change. A clean deck must be labeled `NO_SHIFT_DETECTED_IN_DECK; MODEL_IDENTITY_UNVERIFIED`, never model identity proof. Schema, prompt/context and exposed-snapshot changes must be classified separately from semantic model behavior change.

## Frozen design

- Seed: `6001002`; 200 trials per scenario-policy group.
- Policies: `alias_only`, `metadata_only`, `bracketed_canary`.
- Scenarios: `stationary`, `hidden_in_deck_between`, `hidden_outside_deck_between`, `schema_only`, `prompt_context_drift`, `visible_snapshot_change`, `hidden_in_deck_mid_B`.
- Route schedule is fixed A then B (no order-effect estimate); 200 A rows and 200 B rows, with four retained B positions per trial. Hidden between-block changes start before B; the within-block condition changes after B position 1. All observations are retained even when the policy disposition is HOLD.
- Bracketed canary phases: before A, between A/B, after B. Five fixed deck classes; 20 binary non-action responses per class/trial/phase. Only the target-localization class is changed by the in-deck shift. The out-of-deck shift is deliberately absent from every canary class.
- Route outputs are generated separately from the canary; the hidden semantic shift changes the route outcome distribution. Schema-only changes only schema metadata; prompt/context drift changes only the corresponding hashes and route-output distribution; visible-snapshot control changes the exposed snapshot ID while keeping semantics stationary.
- Candidate threshold: at least 0.20 absolute success-rate decline in any canary class between consecutive bracket phases. Schema and prompt/context checks take precedence; a changed exposed snapshot produces `HOLD_SNAPSHOT_CHANGED` without claiming semantic behavior drift.

## Decision gates

PASS_METHOD_SCOPED requires all of the following under independent raw audit: (1) in-deck between-block change is held before B; (2) in-deck within-B change holds the entire B block; (3) stationary controls are not flagged and retain the narrow no-shift wording; (4) out-of-deck change is not described as broad stability or identity proof; (5) schema-only, prompt/context and exposed-snapshot controls are distinctly typed, not mislabeled semantic shift; (6) alias-only/metadata-only clean outputs do not claim behavior verification; (7) all A/B rows and canary attempts remain in the audit denominator.

The auditor must independently recompute policy disposition, check group/trial/deck completeness and evaluator-truth provenance, and reject altered decisions, dropped route rows and tampered truth. Any source change after this freeze invalidates the run and requires a separately retained construction/failure record before a new freeze.
