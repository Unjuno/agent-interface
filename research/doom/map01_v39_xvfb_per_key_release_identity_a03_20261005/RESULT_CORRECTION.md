# A03 auditor classification correction

The candidate's first outcome is retained unchanged as `results/A03/RAW.json`: `CANDIDATE_ERROR` with `AttributeError: detail`, zero client edges, and Xvfb exit 0. The first auditor source treated all incomplete candidates as `FAIL`, contrary to `PREREGISTRATION.md`, which classifies setup/import/trace/cleanup interruptions as `STOP`.

`SOURCE/audit_v2.py` corrects only that classification and records the candidate raw SHA, status, edge count, and cleanup. It runs once against the unchanged raw A03 outcome. `AUDIT_CORRECTION.json` binds auditor v2 to the unchanged A03 freeze and records auditor v1's SHA without replacing either source. The candidate is not rerun. This is a harness trace STOP, not a release-order mismatch and not a success.
