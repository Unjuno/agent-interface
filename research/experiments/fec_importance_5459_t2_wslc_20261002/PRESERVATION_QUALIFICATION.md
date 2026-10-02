# Historical preservation qualification

This sidecar accompanies preservation of PR #6454 at original head `0b0fcacca28ac2d8c35e87e98bb2afb15f48fad4`. The 18 original package files, recorded invocation outcomes, and `FAIL_METHOD` disposition are retained unchanged.

## Unreconciled source/output discrepancy

The original REPORT, FREEZE, STOP and formal/RUN_RECORD.json record 8,224 audit errors. Static inspection of the committed formal/audit.json errors array finds 8,218 entries: 4,120 `context_importance_labels` and 4,098 `decoded_values`. Both the original recorded count and the committed output are preserved; this note does not replace either with a corrected audit.

The report attributes some failures to invalid-context empty-object/null differences. The frozen formal/source/auditor.py guards its decoded-value comparison with `_meta_ok(ctx)` at lines 285–289, and the committed audit array contains no decoded_values errors for those invalid-context cases. The source/output provenance and discrepancy remain unreconciled.

## Claim and verification boundary

This is historical failure-record integration. Recorded construction success and candidate exit 0 do not override independent audit exit 1 or validate paired wins, transport benefit, FEC performance, or general COMPLETE eligibility. The synthetic, decision-specific limits of Issue #5459 remain in force.

No experiment, candidate, auditor, construction test, or scientific recomputation was run for this preservation review. Large formal/raw.json was not fully retrievable through the review connector, so this review makes no full raw-content revalidation claim. Git blob identity can establish unchanged custody across integration, not scientific validity. Frozen outputs and thresholds were not edited; repair requires a separately preregistered successor as specified by STOP.md.
