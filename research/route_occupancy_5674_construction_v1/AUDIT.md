# Raw-only arithmetic audit

This audit reads only `result.json`; it does not import or execute `check.py`. It independently enumerates the four three-step paths ending in recovery per route from separately stated rational transition matrices, recomputes both probabilities and their gap, and checks the published scope/null fields. Three in-memory corruption controls alter the gap, scope and null-control value and are rejected.

Execution: `docker run --rm --network none --read-only --mount type=bind,source=<directory-containing-audit_raw.py-and-result.json>,target=/work,readonly python:3.12-slim python -B /work/audit_raw.py`. The local first run used the equivalent `issue5674_audit_raw.py` and `issue5674_result.json` names in the bind directory; exit 0. Local stdout:

```json
{
  "audit": "RAW_ONLY_SCOPED_PASS",
  "candidate_imported": false,
  "independent_path_enumeration": true,
  "corruption_controls_rejected": 3,
  "empirical_hypothesis": "UNTESTED"
}
```

Image identity and construction command are in REPORT.md. This is independent arithmetic/readback within an authored finite model; both programs use the same authored transition probabilities. It cannot validate those probabilities for a real GUI or route, nor establish task-level safety or outcome. The issue's empirical H remains untested.
