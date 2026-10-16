# Construction TDD red evidence

This is not the frozen A07 audit run. It records the test-first check against the exact retained A06 auditor source.

Command:

```powershell
python -B research/doom/v39_v15_release_identity_a07_20261005/tests/test_identity_binding.py -v
```

Observed before implementing A07:

```text
test_admission_id_mismatch_is_rejected (__main__.PriorAuditIdentityRegression.test_admission_id_mismatch_is_rejected) ... FAIL

FAIL: [] is not true : A06 must reject an admission whose identity has no matching release

Ran 1 test in 0.015s
FAILED (failures=1)
```

The mismatch changed only `id` on one `input_admission` row in an in-memory copy of the retained A02 raw. A06 returned no failed checks. The raw file and previous A06 output were not changed.
