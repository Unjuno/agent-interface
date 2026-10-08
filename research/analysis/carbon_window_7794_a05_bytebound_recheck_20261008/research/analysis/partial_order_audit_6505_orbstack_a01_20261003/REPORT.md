# Issue #6505 — audit-only A01 report

## Disposition

**STOP_OUTPUT_NOT_EMPTY_OR_MISSING.** The sole A01 invocation exited 1 because `container_config.json` was mistakenly placed in the mounted output directory, violating the frozen auditor's required-empty-output precondition. The guard stopped before reading inputs: archive reconstruction did not occur and zero of 11,111 rows were parsed. This is an operator setup STOP, not a scientific FAIL or audit result. A01 will not be retried; any further attempt requires a separately frozen successor allocation.

Pre-formal construction tests: 7/7 pass on macOS arm64 / CPython 3.14.5. These check the fresh model's finite-state count, a selected independent/dependent pair, Git blob hashing, topological-order discriminator, and all eight effective control values. They do not parse/recompute the 11,111 formal rows. The workspace analysis index passes at 550 retained result/failure directories after the latest-main integration.

Full local Analysis Index workflow suite: 18 test commands / 111 tests passed on the frozen latest-main base. The workflow's pinned historical source was restored temporarily for provenance tests, then the committed source was restored and independently verified. The earlier manually transcribed test-directory typo is retained as a separate failed command attempt and is not counted as a test failure.

Main later advanced to `8acd49301826466e2c8a000c792d19ffce0b17ca` with an unrelated archived raw-log/recovery note. On that exact base the analysis index and this package's 7 tests were rerun and passed; no formal input or auditor source changed.

## H / T / D / C / U

See `PREREGISTRATION.md`. The scope is an independent audit of #4889's retained finite reducer evidence. The predecessor's `HOLD_AUDIT_CONTROL_HARNESS`, raw data, and 7/8 control result remain unchanged.

## Execution and validation

The verbatim first stdout, exit code, and invocation record are in `results/formal_01/`. The container exited without OOM. See `FREEZE.json`, `RUNBOOK.md`, and `CONSTRUCTION.json` for frozen inputs and pre-formal checks. This package does not rerun the original candidate, original auditor, or reducer.

## Limits

Even a `PASS_INDEPENDENT_AUDIT_SCOPED` result would independently corroborate the retained finite table only. It would not establish real trace/GUI replay safety, a product guarantee, latency or storage savings, or authority to relax ordering in runtime systems.
