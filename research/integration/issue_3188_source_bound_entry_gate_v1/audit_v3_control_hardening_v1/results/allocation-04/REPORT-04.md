# Allocation 04 — setup STOP

- Allocation: `issue3188-audit-v3-control-schema-20260921-04`
- Outcome: `STOP_TEST_FIXTURE_PATH_MAPPING`
- Suite invocation: exactly one
- Test cases started: 0
- Setup errors: 1
- Assertion failures: 0
- Docker: not run; Docker daemon unavailable.

The frozen suite failed in `AuditV3ControlTests.setUpClass` before test discovery/execution because the host harness's virtual root used doubled path separators and its frozen `raw.json` path mapping did not match. No assertion ran. The runner's generic `FAIL_AUDIT_V3` label is not the scientific classification: this is a harness/setup STOP. Allocation 04 will not be rerun, and no post-freeze source changes are made.

Formal-02 raw SHA-256 is unchanged before/after: `8460a9ca79611929cbd6d2f6930067a06c6f177e7da3287ad07d1b7f483cb324`. Formal-02 remains `HOLD_FROZEN_AUDITOR_DEFECT`; allocations 01–03 retain their separate pre-discovery STOP records.
