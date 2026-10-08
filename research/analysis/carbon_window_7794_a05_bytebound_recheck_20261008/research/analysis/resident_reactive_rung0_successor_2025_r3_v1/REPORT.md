# Resident-reactive Rung 0 successor #2025 — row-retained successor

Status: PASS_RESIDENT_REACTIVE_MECHANICS_SCOPED

This successor retains all 64 finite rows (16 Boolean predicate traces × 4 stale-generation message timings) in RESULT.json. The audit independently recomputes the false→true edge oracle and compares every stored resident row, stale rejection count, and terminal release against that oracle. It is a finite synthetic mechanism check only.

Formal container execution remains HOLD_DOCKER_UNAVAILABLE; no model, GUI, runtime, network, task-input, latency, token, production-safety, or cross-domain claim is made.

## Reproduction

Run python experiment.py to regenerate the row summary, then python audit.py to verify the retained RESULT.json rows independently.
