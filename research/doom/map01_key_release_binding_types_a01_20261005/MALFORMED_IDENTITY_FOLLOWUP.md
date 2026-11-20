# Post-run malformed identity follow-up

This additive follow-up addresses the unhashable key-up identity case reported on PR #7800 while preserving the A01 candidate, oracle, test file, checksum manifest, and retained outputs byte-for-byte.

- **H:** In the synthetic JSON receipt reducer, key-up `admission_id`, `execution_id`, and `key` values must be non-empty strings before they are used in tuple or mapping lookups. Arrays and objects are valid JSON values but are invalid identities.
- **T:** Reproduce the retained candidate and independent oracle raising `TypeError` for an array `admission_id`. Then exercise separate hardened wrappers against arrays and objects in each of the three identity fields.
- **D:** The follow-up passes when both hardened paths return `FAIL / invalid_up_context_type` for every malformed identity, while the retained frozen paths still reproduce the original exception and all five A01 regressions remain green.
- **C:** The change only covers key-up identity scalar types. It does not establish handling for every malformed outer JSON shape or runtime producer behavior.
- **U:** This is deterministic synthetic contract evidence only. Runtime identity emission, physical key release, timing, GUI effect, recovery, and product safety remain untested.

The hardened candidate and auditor live in `candidate_hardened.py` and `audit_hardened.py`; they validate the key-up identity fields before delegating to their respective frozen A01 paths. The auditor wrapper does not import the candidate. `test_malformed_identity_followup.py` preserves the reproducer and checks both independent paths. No formal allocation or historical A01 output was rerun or rewritten.

## Verification

- `python -m pytest -q test_type_aliases.py test_malformed_identity_followup.py` — 7 passed (Python 3.12 on Windows).
- `python -m py_compile candidate_hardened.py audit_hardened.py test_malformed_identity_followup.py` — passed.
