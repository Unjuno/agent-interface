# Privacy-preserving failure discovery and adversarial integrity

## Feasibility result: #6549

The finite T0 is `PASS_METHOD_SCOPED` and was integrated by merged [PR #6638](https://github.com/Unjuno/agent-interface/pull/6638). It evaluated eight authored cohort histograms at three offsets (`eta={0,1,2}`), for 24 rows; construction checks passed 6/6 and a separate raw-only auditor reconstructed 24/24 rows with zero errors. The conditional user-level `(epsilon=1, delta=0)` singleton inequality gives an exact-label discovery ceiling of zero when absent-mode false-report probability `alpha=0`; requiring discovery `beta=0.9` implies `alpha >= 0.331091497`. This is a theorem applied under its stated premise, not verification of a deployed mechanism.

The tested arm explicitly assumes **no DP guarantee**: `eta` is not sampled DP noise. The deterministic sensitivity illustration retains a predeclared merged category at support 4 across offsets, while singleton/split-taxonomy/correlated/duplicate/low-support cases remain UNKNOWN. The no-failure fixture does not establish population absence. No real telemetry, user data, fleet, GUI, model, or privacy guarantee was tested. See [Issue #6549](https://github.com/Unjuno/agent-interface/issues/6549) and the [retained package](../../research/analysis/privacy_discovery_6549_t0_v1/).

## Successor proposal: #8877

**Status:** Open, unverified security-transfer and evaluation-method idea; no result or deployment claim.

#8877 asks whether the #6549 privacy–discovery frontier survives a bounded adversarial-contributor budget. It freezes the privacy mechanism, cohort, class vocabulary, and release thresholds from a selected #6549-compatible arm, then varies adversarial contribution power. Proposed attacks include false-class inflation, selective suppression or label substitution, alias/split fragmentation, duplicate reports, and adaptive targeting after previous aggregate releases. Benign non-IID/version-correlated cohorts are controls so robustness does not simply suppress legitimate rare subpopulations.

The issue distinguishes authenticated-contributor corruption from unauthenticated Sybil multiplicity; Sybil resistance is not assumed. Exact counts, the frozen non-robust privacy arm, conservative contamination intervals, and a compatible robust heavy-hitter comparator are separate arms. A secure sum may hide individual contributions but does not itself prevent poisoning, and cited robust frequency algorithms do not automatically compose with the privacy/reporting semantics.

No candidate, auditor, or allocation result is reported for #8877. Any future result must retain privacy accounting, honest/adversarial counts, released classes/intervals, false inclusion, true-class suppression, and UNKNOWN distinctly. See [Issue #8877](https://github.com/Unjuno/agent-interface/issues/8877).

## Evidence boundary

#6549's finite method pass is not a DP guarantee, real failure-mode discovery utility, causal attribution, severity estimate, safety certificate, or permission to collect telemetry. #8877's proposal does not retroactively change the #6549 allocation and has not tested an adversarial coalition.
