# A01 preflight STOP

The frozen A01 runner invocation exited 1 while importing the candidate because `lease_cause_v1.py` was absent from its source snapshot. `executor_v13_admission_baseline.Executor` never imported; `submit` was not called, no backend work began, and no `RAW.json` exists. The stderr, exit code, and original pre-run freeze are retained here. A02 adds the missing exact-source dependency and uses a separate run ID.
