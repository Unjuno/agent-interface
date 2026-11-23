# Issue #57 current-main Docker/Linux public MCP contract R02

R01 had one failure only in the combined optimized test bundle: a worker-entry event exceeded the test's 2 s wait. Current main changes this test's cross-thread event coordination to asyncio events. This packet freezes current-main code and reruns the same combined modules once normally and once under `-O`, in the existing locally cached Linux image with networking disabled and source mounted read-only.

`CONDITIONS.json` is the frozen protocol. `run_experiment.py` refuses source/main/image drift, performs a Python preflight, and retains stdout/stderr/exit bytes for both runs. `audit_evidence.py` checks hashes and test counts. No live UI, provider or task input is involved.
