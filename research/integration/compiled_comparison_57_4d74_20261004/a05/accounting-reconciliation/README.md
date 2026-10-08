# A05 per-arm cost reconciliation

This is a read-only reconciliation of merged #7413/A05 retained JSON at source revision `58bcbb4c45501880db8782158ddd3add3b765984`. The script reads the pinned `RETAINED_EVIDENCE_AUDIT.json` arm aggregates (including saved-task counts, task usage, task elapsed time, model labels, and scorer counts) plus the six separate schema-preflight JSONs (A/B/C only). It checks that the reconstructed 26 provider attempts equal the published all-attempt usage totals; it does not directly read the 48 individual task JSON records.

An independent direct-raw-row audit separately read the 48 task JSONs, eight independent-evaluation JSONs, six preflight JSONs, 26 raw model-call results, and `HOST.json`; it reconstructed the same per-arm attempts/totals and matched the joined task-plus-preflight usage exactly. That is a separate audit, not an input to this script.

Run from a full repository checkout with the pinned revision present:

```powershell
python -B research/integration/compiled_comparison_57_4d74_20261004/a05/accounting-reconciliation/reconcile.py > research/integration/compiled_comparison_57_4d74_20261004/a05/accounting-reconciliation/ARM_COST_RECONCILIATION.json
```

## Results

- Reconciles all 26 model attempts and the published totals exactly: input 343,542; output 2,040; cached input 245,248 (subset); reasoning output 1,288 (subset); cache-write input 0.
- Arm A: 14 attempts, 187,626 task+preflight input/output tokens, 126.104 s task elapsed plus preflight wait, 12/12 independent exact effects.
- Arm B: 6 attempts, 78,874 task+preflight input/output tokens, 112.297 s task elapsed plus preflight wait, 12/12 effects.
- Arm C: 6 attempts, 79,082 task+preflight input/output tokens, 142.659 s task elapsed plus preflight wait, 9/12 effects.
- Arm D: no model attempts, 29.764 s task elapsed, 12/12 effects; human setup cost is unavailable.

B versus A reduces these fully joined input+output tokens by 57.96% and task-plus-preflight-wait by 10.95% in this two-block sample. C costs 0.26% more joined input+output and takes 27.04% longer than B, while failing three tasks. The C correctness failure makes it ineligible for an efficiency claim. These values exclude process startup and final independent scoring; cached/reasoning figures are not added to input/output.

## Limits

This is a retrospective four-arm comparison reconciliation, not a predeclared bundle interaction study. It does not add rows to `research/evolution/bundle_evaluations.csv`; that register's study-manifest and measured-combined-arm contract is not met here. No weighted score or new gain claim is introduced.

This reconciliation uses retained post-run JSON and proves internal arithmetic/joins only. It does not establish original-host provenance, authority, arbitrary collateral-content safety, privacy/redaction, or human setup cost. It does not replay model/provider/GUI activity and does not change A05's REJECT decision for fixed crop-OCR.
