# Issue #6680 T0 status — `HOLD_RESOURCE_BEFORE_FORMAL_START`

This is a preformal status report, **not** a scientific PASS/FAIL and not a result. Formal candidate/auditor/container/retry counts are 0/0/0/0. The issue hypothesis remains untested.

The local construction suite passes 4/4 after one retained pre-freeze auditor defect was corrected. One attempted `exec` working-directory route did not apply to the new worktree; unittest discovery failed to import the test module before any candidate/auditor invocation. Re-running discovery with an absolute `-s` path passed 4/4. A separate host CLI construction smoke emitted 20 rows and the local audit returned `PASS_METHOD_SCOPED`; it is not formal evidence and its temporary raw is not promoted. Full construction history and exact commands are in `CONSTRUCTION_LOG.md`.

Formal execution is held because this macOS host has no WSLc and concurrent Docker/OrbStack workloads are visible without an exclusive assignment. The allocation will not borrow another task's machine or shared Engine. Exact H/T/D/C/U, run gates and the required isolation are in `PREREGISTRATION.md`; observed runtime and counts are in `RUN_RECORD.json` and `HOLD_RECORD.md`.

No live GUI, gameplay, model, GPU, CUDA, physical input, authority change, or runtime implementation was involved. Any future T0 must use a distinct authorized container allocation and preserve this HOLD record unchanged.
