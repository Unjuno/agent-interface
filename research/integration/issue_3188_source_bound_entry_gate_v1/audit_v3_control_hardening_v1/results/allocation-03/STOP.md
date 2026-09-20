# Allocation STOP — Issue #3188 audit-v3 control-schema v3

Runner preflight stopped while assembling frozen input hashes. The byte-identical runner requires payload keys `protocol` and `candidate_audit`; the custom host wrapper supplied `protocol3` and `candidate`. No unittest discovery or test case started.

- Status: `STOP_RUNNER_PAYLOAD_ALIAS_MISMATCH`
- Suite attempts: 1; test cases started/completed: 0/0
- This is a host harness payload-map STOP, not a candidate result.
- Formal-02 raw remains unchanged at SHA-256 `8460a9ca79611929cbd6d2f6930067a06c6f177e7da3287ad07d1b7f483cb324`.
- No retry under allocation `issue3188-audit-v3-control-schema-20260921-03`.

Allocation 04 will freeze exact runner/payload key-set preflight before invoking the unchanged five-test suite. Docker validation remains outstanding.
