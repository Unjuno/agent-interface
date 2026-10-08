# #4150 repair allocation ID002 — preformal source freeze

- allocation: `target-belief-admission-4150-20260923-02`
- predecessor ID001: `STOP_LOCAL_SOURCE_MATERIALIZATION`, scientific rows 0/64; never rerun
- repair factor: source materialization only from the exact commit-pinned ID001 GitHub source capsule, plus fresh allocation/publication identity
- formal invocations at ID002 freeze: **0**
- excluded repair construction: **6/6 PASS**, py_compile PASS
- deterministic source tar.xz bytes: **6,228**
- source tar.xz SHA-256: `bfd842df86e78d7bf3ef0b5c5b3fcffd80f0126a6762fbb10a6eebe659d24901`
- Base64 text SHA-256: `828c7ab683572954f5a51286e74f243d71cdd1182054d3b81762a68e23f1452e`
- FREEZE.json SHA-256: `76ef536dac3bea9558395ce88d85342b68e8878b65cd2ca0ce204383aa11d7c3`

The source capsule contains `PLAN.md`, `experiment.py`, `audit.py`, `controls.py`, `test_contract.py`, `ENVIRONMENT.json`, `SCHEDULE.json`, `CONSTRUCTION.md`, `FREEZE.json`, and `SHA256SUMS.preformal`.

The frozen audit/controls/tests/environment bytes are exactly identical to ID001. `experiment.py` differs from ID001 only in the allocation string `-01` -> `-02`; after normalizing that string the files are byte-identical. Thresholds, score profiles, candidate/oracle/comparator, row schedule, and decision gates are unchanged.
