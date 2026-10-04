# Corrective audit-v2 run record

- Purpose: address the three blocking review findings on PR #7675 without rerunning or modifying the retained candidate.
- Inputs: original `INPUT.json` and `CANDIDATE.json`, bound by SHA-256 fields in `AUDIT_V2.json`.
- Command: `python3 audit_v2.py > AUDIT_V2_STDOUT.txt` (one invocation).
- Candidate invocations in this supplement: 0. Original candidate output and v1 audit bytes remain unchanged.
- Audit-v2 independently derives state dispositions from raw events, checks same-final-state/distinct-history claims and every output field, then rejects eight independent corruptions.
- This is a corrective read-only audit supplement, not a new candidate experiment or a live result.
