# Audit V2 test first attempt

The raw-only `audit_v2.py` independently passed, but the accompanying mutation-test runner had one setup error: `test_baseline_error_corruption_rejected` attempted to assign into the tuple returned by `data()`. Five other audit tests passed. The failure was in the test harness, not the auditor result. The first-pass `AUDIT_V2.json` and this note are retained. The test now converts the copied tuple to a mutable list before altering the baseline stderr field.
