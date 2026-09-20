# Allocation STOP — Issue #3188 audit-v3 control-schema v1

The frozen host-suite invocation stopped before test discovery. Python rejected the ephemeral `importlib` loader because it implemented `exec_module()` without the required `create_module()` method.

- Status: `STOP_TEST_HARNESS_IMPORT_ERROR`
- Frozen unit-test attempts: 1
- Test cases started: 0; completed: 0
- This is not a candidate FAIL or PASS.
- Formal-02 raw remains byte-identical at SHA-256 `8460a9ca79611929cbd6d2f6930067a06c6f177e7da3287ad07d1b7f483cb324`.
- No retry will occur under allocation `issue3188-audit-v3-control-schema-20260921-01`.

A distinct successor allocation may reuse the byte-identical frozen auditor and tests with a corrected, independently hashed test loader. Docker/container validation remains a separate outstanding gate.
