# Applicability envelopes for scoped guard evidence

Issue #8631 asks whether learned, falsification-tested applicability assumptions can expose when a scoped guard result is supported only on a narrow trace stratum. The method is diagnostic: it cannot grant authority, relax a guard, or turn missing support into a PASS.

## Falsification-tested applicability envelope — #8631

- **Status:** open transfer proposal; T0 A03 is `PASS_METHOD_SCOPED` for its finite authored fixture. The evidence is integrated in merged PR #8633, while production applicability and external generalization remain unverified.
- **Source:** [Issue #8631](https://github.com/Unjuno/agent-interface/issues/8631); [merged evidence PR #8633](https://github.com/Unjuno/agent-interface/pull/8633); [retained A03 report](../../research/analysis/applicability_envelope_8631_t0_a03_20261008/REPORT.md).
- **Idea:** Learn a compact boundary over trace predicates from labeled training rows, then independently falsify it and audit support per stratum. Reuse classifications remain `WITHIN_SUPPORTED_ENVELOPE`, `OUTSIDE_ENVELOPE`, or `UNKNOWN_SUPPORT`; a finite absence of counterexamples cannot establish universal applicability.
- **Outcome:** A01 candidate execution found a planted failure, but its auditor stopped before audit on an input-contract error (`STOP_AUDITOR_INPUT_CONTRACT`); no retry or scientific result. A02 repaired the input convention but used a hand-authored boundary, so it remains construction-only. A03 trained a one-atom `target_current=true` predicate on five positive and one negative row. The independent raw-only auditor reconstructed 10/10 checks with zero errors; falsification found both planted in-envelope failures (version drift on route A and failure on held-out route B). Stale support with one success/zero failures and an empty stratum remained `UNKNOWN_SUPPORT`; the declared irrelevant noise feature did not change the predicate. This is finite authored-fixture evidence only: no empirical guard calibration, GUI safety, external generalization, runtime behavior, speed, or authority effect was tested. The Issue remains open.

## Relation to neighboring work

#8631 is an evidence-reuse diagnostic, not another component-contract format (#5328), action-prefix safety contract (#5317), or backward-derived observable-precondition model (#6256). It addresses narrow/absent support concerns noted by #2509 and #3312 but does not revise their historical results. Its finite learned boundary can find counterexamples; it cannot prove that an unobserved stratum is safe.
