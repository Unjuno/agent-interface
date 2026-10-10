# Candidate/auditor v1 correction

The first candidate (`candidate_v1.py`, `raw.json`, `CANDIDATE_v1.stdout.log`) correctly exercised acceptance-first ordering, but it evaluated `latest()` only while serializing the final result, after the second monitored wait. It mislabeled that value as the value at acceptance. The v1 auditor (`audit_v1.py`) did not check the time at which that field was sampled. Preserve the v1 artifacts as-is; do not use that field or audit as evidence.

Candidate v2 captures `latest()` immediately when the acceptance helper returns and independently checks the boundary snapshot against the frozen event order. The admission ordering disposition is unchanged; v2 corrects only the evidence capture and audit.
