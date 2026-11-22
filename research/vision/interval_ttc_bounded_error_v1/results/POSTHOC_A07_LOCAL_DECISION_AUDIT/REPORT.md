# Issue #8157 A07 local decision audit

**Disposition: `AUDIT_INTEGRITY_FAILURE_MUTATION_CONTROLS`.** The pinned A02 input hashes, A04 report hash, profile structure, and all 2,400 prefix reconstructions passed. The posthoc score calculation completed, but two of six mutation controls failed, so the diagnostic counts and label are not accepted as a scientific interpretation.

The first mutation control expected a threshold below 1.0 even though the calibration control's score was 2.5 and the evaluation control at 1.0 is intentionally excluded. The correct calibration-only threshold in that fixture is 2.0. The paired-lead corruption set the first interval upper endpoint to 2.1 while the mutated calibration threshold also became 2.1; the interval therefore still yielded on the first prefix and did not violate lead. These are test-fixture defects, not evidence about the estimator.

A07 ran once and exited 2. Its raw report is preserved for diagnosis only. No candidate, generator, prior auditor, container, or runtime ran. A02 remains formally `FAIL_METHOD` and unscorable. A07 will not be rerun or edited; any corrected audit is a separately frozen successor.
