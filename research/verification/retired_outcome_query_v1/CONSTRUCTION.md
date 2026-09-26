# Preserved construction and preformal changes
One construction invocation:16 cases, actual runner exit0, stderr empty.
Original RAW.jsonl SHA25692c7896437667cf809807cbb416a7218454e96c001a5933cb8e6143819ea7464.
Ten policy unittest methods passed (UNIT.stderr), exit0.
Initial independent auditor exited1: in BOOLEAN_EPOCH it incorrectly attached
an epoch7 receipt despite actual SQL binding true as1, which found no receipt.
Original audit_before_fix.py and AUDIT.json are retained. Corrected projection
matches epoch/op_id from the actual read query; also made command comparisons
JSON-type-sensitive. AUDIT_v2.json exits0, PASS_CONSTRUCTION_ONLY,16 rows, errors[],
12/12 corruption controls rejected. No receiver/policy or raw bytes changed.
The auditor was developed after the construction matrix, before formal freeze.

run_before_formal_path_guard.py preserves construction runner source. Preformal
runner now refuses any noncanonical formal output and checks installed runtime
identities in addition to frozen source. This is engineering, not another trial.
No formal outcome existed during these changes. No new supervisor Issue.
