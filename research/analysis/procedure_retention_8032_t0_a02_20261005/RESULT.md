# Result — Issue #8032 T0 A02 ordinal-score power sensitivity

**Disposition: `PASS_METHOD_SCOPED` for the frozen synthetic sensitivity calculation. `HOLD_T1_FEASIBILITY_AND_REVIEW` remains.** There are no participant observations or effects.

The one-shot WSLc candidate ran 54 frozen cells (3 authored ordinal PMFs × 2 target score-scale effects × 9 completer counts) plus one 20,000-replicate null calibration. The WSLc raw-only auditor independently reconstructed all 54 rejection counts and pooled-category digests, verified effect calibration, source identities and intervals, and returned `PASS_RAW_RECONSTRUCTION`, `errors=[]`. Candidate exit 0; auditor exit 0; retries 0. The auditor verifies the null interval against its independent recomputation; a separately retained post-hoc disposition check applies the frozen inclusion gate. The null control rejected 238/20,000 = 0.0119 at nominal alpha .0125; its Wilson 95% interval [.01049,.01350] contains .0125. See [post-hoc gate adjudication](POSTHOC_ADJUDICATION.md); it does not alter candidate or audit output.

The first grid size whose simulated power's Wilson lower bound reached .80 was:

| Authored baseline shape | Target d | Completers/arm | Recruited/arm at 15% attrition | Three-arm recruited total |
|---|---:|---:|---:|---:|
| ceiling | .35 | 180 | 212 | 636 |
| middle | .35 | 220 | 259 | 777 |
| floor-skew | .35 | 220 | 259 | 777 |
| ceiling | .50 | 100 | 118 | 354 |
| middle | .50 | 100 | 118 | 354 |
| floor-skew | .50 | 100 | 118 | 354 |

At target d=.35, the chosen grid threshold differed by 40 completers per arm (212 vs 259 recruits per arm) between the ceiling and other authored shapes. At d=.50 the first qualifying grid point was 100/arm for all three shapes; the ceiling case at 80/arm had estimated power .81 but its lower Wilson bound (.79) did not meet the frozen gate. This is a coarse grid and Monte Carlo sensitivity, not an exact minimum N. A01's normal-approximation point estimates (90/arm at d=.50; 183/arm at d=.35) are not directly interchangeable with these rank-sum grid results.

For comparison with A01's illustrative burden only, 354–777 recruits at 30 minutes each would imply 177–388.5 participant-hours. This omits recruitment, supervision and scheduling and is not a budget, proposal or permission to recruit.

## Interpretation and limits

The result shows that, under these specified synthetic PMFs and the frozen test, a single standardized mean difference does not uniquely determine the grid-based sample-size sensitivity. The assumed common proportional-odds shift, distributions, rank-sum normal approximation, marginal four-contrast alpha, coarse N grid, and 15% attrition are not estimated or validated from people. The four co-primary endpoints' dependence is not modeled; marginal 80% does not imply joint 80%. The simulation does not model critical target errors, final-state mismatch, missing outcomes, baseline adjustment, or treatment-specific effects.

This does not establish human retention, transfer, skill decay, retrieval benefit, recruitment feasibility, or a smallest meaningful effect. Independent human protocol review, exact final analysis/power work, recruitment feasibility, ethics/privacy approval, informed consent and separate authorization remain prerequisites for any T1. A01 remains unchanged; this is a separate additive T0 allocation.
