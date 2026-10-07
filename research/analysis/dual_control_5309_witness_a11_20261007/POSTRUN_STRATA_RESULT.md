# Post-run A11 strata audit result

Diagnostic allocation `5309-TOPOLOGY-DEPENDENT-A11-POSTRUN-STRATA-V2` completed once against retained bytes. Verdict: **`PASS_RETAINED_STRATA_RECONSTRUCTION`**; 264 raw rows checked, zero reconstruction errors, zero unsupported completions. Input, choices, raw and oracle SHA-256 values are embedded in `audit_retained_strata_v2.json`; the diagnostic script and output hashes are in `POSTRUN_STRATA_SHA256SUMS.txt`.

| Corrected stratum | Cases | Generic completions | WITNESS completions |
|---|---:|---:|---:|
| Correct prediction, at least one preserving action affordable | 15 | 9 | 15 |
| Correct prediction, preserving action(s) all over budget | 3 | 0 | 0 |
| Correct prediction, no preserving action exists | 15 | 0 | 0 |
| Misspecified prediction | 33 | 9 | 3 |
| Prior witness | 66 | 66 | 66 |

This corrects the descriptive group labels in the frozen A11 auditor/report: their “correct affordable” bucket was 6/12 and “over budget” 3/3 because it tested the cost of `action-b` rather than the cost of the actual preserving action. Those labels are not retained as accurate descriptive strata. The original one-shot `audit.json` still says `FAIL_AUDIT` because its preregistered misspecification gate required zero WITNESS completions; the post-run diagnostic does not change that formal result, and no candidate/environment/auditor stage was rerun.

The corrected data show an affordable-stratum increment of 6 completions (15 vs 9) and no benefit in the three truly over-budget cases (0 vs 0). In the misspecified stratum, WITNESS completes 3 of 33 cases because those selected transitions actually reach the witness state; none is unsupported. This is post hoc descriptive evidence from an authored finite fixture, not a new preregistered result or broader hypothesis pass.
