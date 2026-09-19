# Resident-reactive Rung 0 successor #2025

Status: PASS_RESIDENT_REACTIVE_MECHANICS_SCOPED

The finite runner enumerates 16 predicate traces × 4 stale-generation message timings = 64 rows. The resident arm fires exactly once per declared false→true edge, rejects the stale message by construction, and emits a terminal release in every row. The independent audit recomputes all 64 row counts and the edge oracle.

The result is only a finite synthetic mechanism check. It makes no model, GUI, runtime, token, latency, production-safety, or cross-domain claim.

## Reproduction

`python experiment.py`
`python audit.py`

The first outcome is retained in `RESULT.json`; no rerun or tuning was used.
