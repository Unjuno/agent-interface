# Construction record — preformal

Allocation: `belief-external-transition-5368-t0-hostcpu-20261003-a01`

Frozen base: `main@3729d6825e67b7276b58d40ef6c125e4a3b441bf`

## Construction-only verification

Environment: Microsoft Windows 11 Home, build 26200; Python 3.12.10; standard library only. Command, run from this directory:

```powershell
python -B -m unittest -v test_construction.py
```

Outcome: **6/6 PASS** in the first run (0.010 s) and **6/6 PASS** in a second run (0.006 s) after strengthening the auditor's mutation-control harness. Checks covered the exact nine-case inventory and unique IDs, trace lengths/endpoints, all predeclared scenario categories, transition trace consistency except the intentional complete-model contradiction control, absence of formal outputs, and Python AST parsing. These checks did not import or invoke `candidate.py`, `runner.py`, or `audit.py` and are not the formal result.

WSLc was available (`wslc 3.0.1.0`) but not invoked because #5085's current resource-coordination hold is explicitly still respected by the latest #5368-related PR #6775. The WSLc container list was empty at preflight, but idleness is not an allocation. Its cached `python:3.12-slim` image (`python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`) was inspected but not run. Windows reported 1.49 GB free physical memory at preflight; the host-only T0 is deliberately limited to nine short finite rows. No WSLc cgroup/swap behavior is claimed because WSLc was not invoked. The local CPU T0 is independent of GPU and WSLc allocation. The candidate formal and auditor invocations remain 0 at this construction stage; no retry or run output exists.
