# Issue #5771 — T1 allocation-03

This successor preserves allocations 01 and 02 unchanged. Allocation-01 stopped before any step because its dispatch job condition was stale. Allocation-02 ran the pinned candidate once, but the raw-byte gate expected a Windows CRLF byte; Linux emitted LF. Its exact raw (9,231 bytes, `e6e35e…`) is now retained on main through PR #5802, but was not audited in that run.

Allocation-03 keeps the exact v1 candidate, fixture, and independent auditor blobs and changes only the preregistered raw expectation to the retained Linux bytes. Results are written to this v3 path. See [v1 PLAN](../disturbance_response_5771_t1_v1/PLAN.md) for H/T/D/C/U. This remains a synthetic finite method construction, not GUI coverage or a safety claim.
