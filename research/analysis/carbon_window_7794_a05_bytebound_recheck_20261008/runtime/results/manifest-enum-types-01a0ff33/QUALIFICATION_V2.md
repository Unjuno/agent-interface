# Supplemental audit v2 — review correction for #6860 / #6854

The original `audit_matrix.py` uses Python dictionary equality. It correctly
reconciled the retained records and rejected its ten declared controls, but it
does not preserve JSON scalar types: `False == 0 == 0.0` and `True == 1 == 1.0`.
Non-author review on head `5821ec3adaa01a44a13011bdf1f069b716441981`
reproduced four accepted corruptions. This worker reproduced those and five
additional copies before repairing the auditor: three test methods, nine failing
subtests, exit 1. The result limits the original audit's coverage; it does not
change the actual runtime refusal outputs.

`audit_matrix_v2.py` is a separately versioned raw-only auditor. It compares
object/list structures recursively and requires identical scalar Python types
from JSON decoding at every node. JSON object key order remains immaterial.
Boolean/integer and integer/float substitutions are distinct. The API input
identity and expected validation/admission/readiness outputs use this comparison.
It still imports no runtime, candidate or candidate tests.

No original file in the previous PR head was changed. The original auditor,
`audit.json`, before/after raw, fixture, runtime guards, tests, manifests and logs
retain their exact Git blob identities. Original local logs remain private;
new public test logs redact only private checkout/home prefixes.

## Decision and executed evidence

- H: recursive type-sensitive comparison rejects equal-valued JSON scalar
  substitutions without rejecting either unmodified retained record.
- T: three ordinary construction/regression methods; nine copied-raw scalar
  controls; one supplemental read-only audit of both original 77-row records.
  The nine controls were fixed in the test before the v2 comparison changed.
- D: v1 must expose all nine blind spots; v2 must reject all nine, accept both
  originals, and retain rejection of all ten original controls.
- C: numeric equality may be appropriate for an approximate measured quantity;
  it is insufficient for exact JSON fixture and admission-result identity.
- U: decoded JSON structure/type equality, not lexical identity of arbitrary JSON
  serialization, concurrent files or production backend behavior. Existing SHA
  pins preserve the exact retained raw/fixture bytes separately. Separate audit
  implementation by the same author is not non-author review.

After repair: three test methods pass (exit 0). Supplemental auditor v2 reports
`PASS_SUPPLEMENTAL_JSON_TYPE_AUDIT_SCOPED`: both 77-row records reconcile; baseline
14 TypeError rows and repaired zero remain unchanged; 19/19 copied-output controls
are rejected. `audit_v2.json` retains each reason plus auditor and original raw
hashes. This is a new audit receipt, not a replacement or reclassification of
`audit.json`. No candidate, runtime matrix, formal allocation, model, container,
GUI, GPU or input was rerun for the repair. Main merge gates remain outstanding.

## Reproduce from repository root

```sh
python -m unittest discover -s runtime/results/manifest-enum-types-01a0ff33 -p 'test_audit_matrix_v2.py' -v
python runtime/results/manifest-enum-types-01a0ff33/audit_matrix_v2.py /fresh/path/audit-v2.json
```

The auditor exclusively creates the requested receipt. Keep retained outputs
immutable. PUBLIC_MANIFEST_V2 records the original commit/files and the added
supplemental package hashes; its own bytes are excluded to avoid self-reference.
