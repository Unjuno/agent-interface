# Preserved predecessor disposition: Issue #7678 A01

A01 allocation PREFERENCE-MANIPULATION-7678-T0-20261005-01 remains HOLD and is not edited or reclassified. Its first formal auditor exited 1 because the frozen metadata lacked fixture_sha256; the original auditor stdout/stderr were not retained, and later code/freeze edits plus a diagnostic PASS do not repair that consumed allocation.

The additive review-correction-04 recheck independently verified 7,774 deviation rows, found 7,178 report-dependent certificate changes, and found zero safe-beneficial deviations under the declared possible-frontier set utility in either information partition. It remains non-confirmatory. The issue record and existing integration PR retain the full history:

- [A01 HOLD and future fresh-allocation requirement](https://github.com/Unjuno/agent-interface/issues/7678#issuecomment-5982960226)
- [A01 non-confirmatory review-correction updates](https://github.com/Unjuno/agent-interface/issues/7678#issuecomment-5983810072)
- [Existing A01 evidence PR #7733](https://github.com/Unjuno/agent-interface/pull/7733)

A02 uses a new allocation ID and a new one-shot formal candidate/auditor sequence. It does not import A01 candidate output, invoke A01 code, or overwrite A01 files.
