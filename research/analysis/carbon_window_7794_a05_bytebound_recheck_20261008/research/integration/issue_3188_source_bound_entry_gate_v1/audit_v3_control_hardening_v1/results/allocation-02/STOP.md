# Allocation STOP — Issue #3188 audit-v3 control-schema v2

Runner preflight stopped before unittest discovery: the frozen runner reads `freeze["runner"]["sha256"]`, while `FREEZE-02.json` places that identity under `loader`. No test case started.

- Status: `STOP_FREEZE_RUNNER_SCHEMA_MISMATCH`
- Suite attempts: 1; test cases started/completed: 0/0
- This is a manifest/runner setup STOP, not a candidate result.
- Formal-02 raw remains unchanged at SHA-256 `8460a9ca79611929cbd6d2f6930067a06c6f177e7da3287ad07d1b7f483cb324`.
- No retry under allocation `issue3188-audit-v3-control-schema-20260921-02`.

A separately identified successor may keep byte-identical code and tests while fixing and preflighting only the manifest schema. Docker validation remains outstanding.
