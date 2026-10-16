# Failure-episode unitization sensitivity — #7857

- **Status:** Synthetic method result; real-trace eligibility remains on hold.
- **Source:** [Issue #7857](https://github.com/Unjuno/agent-interface/issues/7857), retained by merged [PR #7907](https://github.com/Unjuno/agent-interface/pull/7907).
- **Idea:** Before assigning mechanism labels to continuous traces, test whether plausible episode-boundary choices change the denominator, failure-mode occupancy, or held-out discovery estimates. Category agreement on already aligned units does not measure boundary agreement.
- **Outcome:** T0 reports `PASS_METHOD_SCOPED` on seven authored synthetic traces. The independent auditor reconstructed 12/9 annotation spans and rejected 5/5 mutations. The custom exact-span F1 was 0.476; conditional category agreement on six aligned units was 6/6. In one training stratum, singleton/doubleton counts shifted from (1,2) to (3,0), and held-out new-mode rate from 2/3 to 1/2. The sensitivity gate flagged the change, but both frozen saturation decisions remained false.

## Boundary and next gate

Exact-span F1 is a custom boundary diagnostic, not Krippendorff's unitizing alpha or a population reliability estimate; the segmenters were synthetic, not human adjudicators. A bounded T1 search returned `HOLD_NO_ELIGIBLE_CONTINUOUS_TRACE`: no reviewed trace family had raw continuous timing, stable identity/provenance, and paired independent episode annotations. No real-trace disagreement, failure-rate, causal, or safety result follows. Reopen T1 only when that source-bound evidence exists. See the retained [T0 result](../../research/analysis/unitization_sensitivity_7857_t0_20261005/RESULT.md) and [T1 eligibility audit](../../research/analysis/unitization_sensitivity_7857_t0_20261005/T1-ELIGIBILITY.md).

## Joint unitization and linkage uncertainty — #8004

[Issue #8004](https://github.com/Unjuno/agent-interface/issues/8004) is a distinct successor to #5826 and #7857. It tests whether uncertainty in within-channel episode boundaries and cross-channel event identity can jointly change an ascertainment estimate even when either one-at-a-time sensitivity is stable.

Its A02 finite T0 reports `PASS_METHOD_SCOPED` and `H_PASS_SCOPED`: the raw-only auditor reconstructed all nine assignment rows and rejected 6/6 mutations. Boundary-only and linkage-only envelopes were `[2,2]`; the joint envelope was `[2,3]` and returned `UNIDENTIFIED` at the frozen threshold. The clean unique-ID control recovered the oracle value exactly. This is an existence result on the authored finite fixture, not a real failure count or calibrated interval. Its evidence is in [Draft PR #8020](https://github.com/Unjuno/agent-interface/pull/8020); the separately retained [PR #8011](https://github.com/Unjuno/agent-interface/pull/8011) is construction-only and is not pooled with A02.

Keep latent event identity, segmentation, linkage, detection, and estimator as separate uncertainty layers. No real-trace eligibility, source independence, population estimate, or safety result follows.
