# T1 A06 result — prompt leakage STOP

Candidate completed the frozen 390-call plan. The independent auditor found 12 premature conflict claims at prefix 4 (per-episode and batch-2, across all three seeds), where source `src-05` / value `published` was not visible yet. The frozen prompt itself names this future evidence and conflict contents, creating leakage. The frozen audit therefore returns `FAIL_METHOD`; no cadence result is valid.

The raw is retained at 390 rows with SHA-256 `6ae1b0539f4e246e4d787ee5d8f1531f1a7eeaf121d8dae8fa61f7ea38bffe6a`. See `AUDIT.json`, `STOP.md`, and `RUN_RECORD.json`. A successor needs generic rules that never name future episode IDs or values, while its frozen auditor continues to check transition fidelity.
