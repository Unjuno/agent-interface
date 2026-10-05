# Independent readback audit version notes

The original candidate/test runs and their receipts were not changed or rerun.

- `audit_retained.py` / `audit-result.json` failed its check requiring byte-identical
  red-v2 and green-v1 stderr. The logs differ only in the nondeterministic
  `Ran 4 tests in ...s` duration; structured stdout and the four test outcomes
  are identical. `audit_retained_v2.py` normalizes only that duration line and
  independently checks both receipt hashes. Its result is retained separately.
- `audit_retained_v3.py` / `audit-result-v3.json` compared the baseline manifest
  to the mutable post-patch source export, so it incorrectly flagged the expected
  patched `session_map01_v12.py`. `audit_retained_v4.py` compares the 56 base pins
  to red-v2's pre-patch runtime source manifest, and checks all green-v2 source
  entries against the post-patch export. It also confirms red-v2's only source
  mismatch with that patched export is the expected session file.

The final readback is `audit-result-v4.json` (PASS). The recorded initial audit
failures remain in their original scripts and result files. No startup matrix,
test suite, owner, or input operation was rerun during these audit corrections.
