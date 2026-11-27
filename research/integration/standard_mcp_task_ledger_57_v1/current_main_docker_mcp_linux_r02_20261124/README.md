# Issue #57 current-main Docker/Linux public MCP contract R02

R01 had one failure only in the combined optimized test bundle: a worker-entry event exceeded the test's 2 s wait. Current main changes this test's cross-thread event coordination to asyncio events. This packet freezes current-main code and reruns the same combined modules once normally and once under `-O`, in the existing locally cached Linux image with networking disabled and source mounted read-only.

R02 passes all 87 tests in both modes. The comparison is test-harness contract evidence, not GUI/provider or task-efficiency evidence. `CONDITIONS-r08.json` is the final audit conditions file; `AUDIT.json` records source/raw validation. `raw-preflight/` preserves harness/auditor setup failures, and `raw-r04/` contains the one normal and one optimized test run.
