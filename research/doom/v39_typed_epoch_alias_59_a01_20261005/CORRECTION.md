# A01 interpretation correction

The frozen decision predicate was correct: accept the exact-integer control, and reject every malformed Boolean/float alias. The raw output shows the control accepted and all eight aliases accepted, so the tested source boundary is fail-open. However, the frozen `FREEZE.json` decision label and candidate `RESULT.json` classification string incorrectly called that outcome `FAIL_CLOSED_EPOCH_IDENTITY_GAP`. This is a label error; it does not change any row, observed result, or pass/fail predicate.

The independent audit's label `PASS_AUDIT_RECONSTRUCTS_SOURCE_FAIL_OPEN` accurately describes its own 53/53 reconstruction. The corrected scientific interpretation is `FAIL_OPEN_EPOCH_IDENTITY_GAP`. Keep the original freeze and candidate result unchanged as the first outputs; this correction is a separate post-run interpretation record. No candidate or auditor was rerun. The earlier exploratory probe remains separately disclosed in `REPORT.md`.

The mislabel weakens the preregistration/output quality, so this A01 should be reviewed as a fail-open observation with a protocol-label defect, not as a clean formal pass.
