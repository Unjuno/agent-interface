# Saved-result audit for the #57 Chromium constructions

This offline auditor checks the two preregistered task-1 outputs retained by
PR #7384: graph crop-OCR seed 991060 and caller-v3 composition seed 991061. It
cross-checks the package hash manifest, exact append-only POST row, all-six
oracle incompleteness, retained screenshot/crop references and hashes, OCR
token observation, fresh target-check sequence, compiled transition IDs and
release receipts, and durable-journal hash chain/call IDs.

Run it from a fully materialized checkout:

```powershell
python -B research/integration/compiled_gui_bundle_57_20261004/a05-saved-result-audit/saved_result_audit.py research/integration/chromium_client_57_4d74_20261004
```

The command verifies all 360 entries in that package's `FILES.json`. An
integrity `PASS` means those saved records are internally consistent and
their listed bytes match the manifest. The scientific decision remains
`HOLD_FULL_MATCHED_COMPARISON`: each output has one exact task-1 POST, while
tasks 2–6 remain missing. The report deliberately does not infer cold/warm
economics, cross-task reuse, repair transfer, or A/B/C/D efficiency.

## H/T/D/C/U

- **H:** the retained one-task records can be reconciled across the saved
  result JSON, screenshots and OCR crops, target checks, durable journal,
  release receipts, and independent POST history.
- **T:** run this read-only auditor against both preregistered result folders;
  require every package hash, action/journal ID, target-check sequence, exact
  task token, and six-task status to agree. Corruption tests mutate these
  boundaries without invoking the browser or model.
- **D:** integrity passes only when all checks agree. The scientific
  disposition remains HOLD until the full matched comparison is run and
  independently scored.
- **C:** these checks can establish saved-byte consistency, not independent
  provenance or whether an unrecorded event occurred. OCR is not rerun here;
  the independent POST row remains the task-effect scorer.
- **U:** the caller result lacks a bounded evidence reference/digest/scope,
  its phase says `cold` while its caller route is labeled `warm_reuse`, and the
  compiled receipt marks raw-evidence retention unverified. The audit reports
  these as warnings instead of concealing them.

## Validation recorded here

The standard-library test file has ten synthetic corruption controls. In
addition, I ran the auditor against a targeted local copy of the two committed
results and the 18 referenced manifest members: it checked both task-1 POSTs,
94 journal frames, screenshots/crops, fresh target checks, transition IDs and
releases with no integrity errors. That targeted run was not a full 360-member
manifest verification. A separate non-author review recorded 360/360 member
hashes at the PR head in [Issue #57 comment 5975732812](https://github.com/Unjuno/agent-interface/issues/57#issuecomment-5975732812).

No GUI, model, provider, or formal allocation is invoked by this package.
