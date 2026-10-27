# Run record

- Allocation: Issue #8630 T0 A01, 2026-10-09.
- Source: candidate/auditor files in this directory; model and decision gate in `FREEZE.json`.
- Candidate invocation: `python3 candidate.py > candidate_raw.json` — exit 0.
- Auditor invocation: `python3 audit.py > auditor_raw.json` — exit 0.
- Reconciliation: candidate's chosen policy/value equaled the independent enumerated maximum in both fixtures. The preregistered weak-signal requirement failed because observation+recovery scored 0.755, above the no-observation+recovery score 0.750.
- Disposition: `FAIL_METHOD`; no formal rerun, no parameter adjustment, no raw replacement.
- Runtime: local macOS Python, CPU; no container was required by this deterministic analytical enumeration.
