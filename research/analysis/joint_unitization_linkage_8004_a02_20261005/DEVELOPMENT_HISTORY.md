# A02 development failures and repairs

The following were observed in the first test run before the final candidate
CLI invocation. They are preserved as development failures, not relabeled as a
formal allocation result.

1. `test_deleted_plausible_link_is_measured_as_missed_opportunity` and
   `test_independent_audit_reconstructs_all_assignments_and_six_opportunities`
   failed with `oracle_expected_detection_mismatch`: the initial oracle encoded
   F5/F6 latent detector targets as if they were observed detections despite
   censoring/missing intervals. Corrected the oracle to store no observed
   detection for these opportunities, keep latent channels separately, and
   retain `?` in their observable-history positions.
2. `test_false_split_or_duplicate_raw_record_is_detected` found that the
   auditor's canonical reconstruction caught a component mismatch but did not
   separately inspect record conservation in the candidate-supplied clusters.
   Added an explicit no-duplicate/exact-coverage check over supplied cluster
   records.

Final candidate and auditor were run once each after these development fixes.
Final normal/optimized suites passed 8/8; `run_audit.json` retains the resulting
independent assessment. Earlier failure text above remains the only retained
record of those construction-test failures; there was no separate first-run
candidate output to preserve.
