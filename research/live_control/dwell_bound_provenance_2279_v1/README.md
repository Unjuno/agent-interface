# Dwell bound provenance successor (Issue #2418)

Successor to #2279 and merged #2402. Tests that finite upper bound M is accepted only with explicit source_id and trusted=true.

## H/T/D/C/U

- H: finite M is usable only when provenance is explicit and trusted.
- T: trusted evidence passes; missing, untrusted, and invalid evidence fail closed.
- D: deterministic native and pinned-container Python tests; no live GUI/model/network calls.
- C: does not prove empirical correctness, censoring, GUI timeout policy, live telemetry, or task/model effects.
- U: live provenance acquisition and GUI dwell validation remain open.

Formal result is emitted by audit.py and CI; failures/stops are preserved in Issue/PR history.
