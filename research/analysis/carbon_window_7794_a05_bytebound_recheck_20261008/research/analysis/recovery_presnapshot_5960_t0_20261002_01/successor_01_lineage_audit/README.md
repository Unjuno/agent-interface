# Audit-only successor — snapshot identity and signal lineage

This successor audits the unchanged parent `candidate_result.json` and preserves the original T0 audit result. It does not rerun the candidate. The independent auditor binds each capture to the exact scenario/seed failure ID, source ID and receipt ID, and checks that diagnosis promotion is supported by the captured signal and eligible cause.

After checking FREEZE.json, run `python -m unittest -v test_lineage_audit.py`, then exactly once run `python run_audit.py`. The formal auditor reads the parent candidate result by relative path and checks its frozen SHA-256. Do not rerun the formal audit; construction tests are separate.
