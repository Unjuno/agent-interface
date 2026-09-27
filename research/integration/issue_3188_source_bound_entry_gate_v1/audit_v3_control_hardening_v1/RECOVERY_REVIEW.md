# Recovery review: audit-v3 allocation 04 STOP

## H / T / D / C / U

**H** — Preserve the abandoned control-hardening attempt as an explicit setup STOP, separate from Issue #3188's formal-02 entry-gate outcome and from any later successor.

**T** — Retain the four freeze records, four protocols, frozen runner/auditor/tests, and allocation 01–04 outcome files unchanged. Add only this review and a link from the parent README. No test suite or formal allocation was rerun.

**D** — Allocation 04 is `STOP_TEST_FIXTURE_PATH_MAPPING`: one suite invocation, zero test cases started, one `setUpClass` error, zero assertions. The generic runner label `FAIL_AUDIT_V3` is not treated as a scientific or auditor assertion failure. The retained formal-02 raw SHA-256 independently recomputes to `8460a9ca79611929cbd6d2f6930067a06c6f177e7da3287ad07d1b7f483cb324`, matching both the frozen input hash and the recorded before/after value. Locally recomputed hashes match the freeze for `runner_v2.py`, `PROTOCOL-04.md`, `independent_audit_v3.py`, `test_audit_v3.py`, the candidate `run.py`, and candidate `audit.py`. Repository workspace index (131 top-level namespaces) and `git diff --check` pass.

**C** — Allocation 04 was a Windows-host auditor-control suite; Docker validation was not run because the daemon was unavailable. No claim is made about container execution, auditor correctness, GUI/X11/input, game recovery, model behavior, or production readiness.

**U / lineage** — Allocations 01–03 remain their distinct pre-discovery STOPs. Formal-02 remains `HOLD_FROZEN_AUDITOR_DEFECT`; its raw result was not modified. This control-schema attempt is not the Issue #3188 32-vector entry-gate execution itself, and its allocation is spent: do not rerun or relabel allocation 04.
