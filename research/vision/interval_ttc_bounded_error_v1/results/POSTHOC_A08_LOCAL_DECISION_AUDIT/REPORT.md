# Issue #8157 A08 retained-raw decision audit

**Disposition: `NO_INCREMENTAL_VALUE_SIGNAL_ON_RETAINED_A02_RAW`.** The A08 auditor verified the three retained A02 files against A04's byte hashes and verified A04's `PASS_RAW_RECONCILIATION_ONLY` report hash. It reconstructed all 2,400 prefixes with zero candidate mismatches, validated all 200 rows and ten profile/split/hazard strata, and passed all six focused mutation controls. A02 remains formally `FAIL_METHOD` and unscorable; this posthoc diagnosis does not change that result.

A08 reports eligible in-model hazard prefixes separately from numeric intervals. Numeric interval coverage was 109/120 (90.8%) in approach, 108/120 (90.0%) in iid, 110/120 (91.7%) in correlated, and 87/100 (87.0%) in irregular/dropout. There were zero in-model containment misses and zero invalid-profile terminal interval false yields.

Calibration-only thresholds were 0.0 s for point secant and interval upper endpoint. On evaluation data, both methods yielded on zero of the 20 eligible in-model hazards. False yields were zero for both methods in each of iid, correlated, and irregular/dropout, so there was no strict false-yield reduction. The paired lead comparison had zero paired rows and no failures; because neither method yielded on an eligible hazard, the required useful-warning gate did not pass.

This is retained-sample synthetic evidence only. It does not establish a TTC method pass, resolve A02's original formal integrity failure, calibrate real visual bounds, or test vision, GUI/game behavior, control, or safety. No candidate, generator, earlier auditor, container, or runtime was invoked for A08.
