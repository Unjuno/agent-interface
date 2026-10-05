# Post-merge review corrections for Issue #7765

PR #7772's T0/T0b raw results and their frozen `candidate.py`, `auditor.py`,
`test_method.py`, freezes, source hashes, and `SHA256SUMS` remain unchanged.
This additive correction addresses two code-review findings without rerunning
either formal allocation:

- `reviewed_candidate.run_trial` returns `yield_unbound_or_stale` with zero
  corrections when the first observation is stale; `act` is not called.
- `reviewed_auditor.audit_rows` returns `HOLD_AUDIT_OR_OUTCOME` before arm-pair
  indexing when the raw pair grid is missing, duplicated, or malformed.

The correction is a reviewed wrapper around the frozen T0 source, so the
historical experiment remains byte-reproducible. `test_review_fixes.py` tests
the new entry points; the original `test_method.py` continues to test the
frozen implementation. No formal candidate or auditor was rerun, and no
scientific disposition or raw result was changed.
- `reviewed_auditor.audit_rows` now requires exact `int` seed identifiers before set comparison, excluding `bool` and `float` values that compare equal to integers. Full-grid `False` and `0.0` mutations both return `HOLD_AUDIT_OR_OUTCOME`.

The complete WSLc package suite passes 11/11. The committed raw JSONL was restored byte-for-byte after the Windows checkout exposed CRLF translation; its frozen SHA-256 matches again. Formal candidates/auditors were not rerun.
