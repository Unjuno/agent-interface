# Additive audit correction

The original `audit.py` / `AUDIT.json` are preserved as audit v1. A mutation discovered on 2026-10-08 showed that v1 accepted three rows when the cancel-write-failure case was replaced with a duplicate of the successful hard-crossing case. The earlier length check did not require unique case names, so the recorded cancel-failure check could be overstated.

`audit_v2.py` and `AUDIT_V2.json` add an exact, unique case-name requirement before validating individual rows. `test_audit_v2.py` includes the substitution mutation, which v2 rejects. The candidate was not rerun; the same frozen `RESULT.json` and source identities were re-audited. The v1 audit is not deleted or rewritten.
