# Issue #6645 — A01 retained STOP

Allocation `CGREF-6645-T0-ORB-20261003-01` stopped before formal execution.
Its construction run exited 1 (11/13 tests passed) and the observed interpreter
version did not match the freeze. See
[`results/preformal_01/STOP.md`](results/preformal_01/STOP.md) and
[`results/preformal_01/STOP.json`](results/preformal_01/STOP.json).

No candidate/auditor formal invocation occurred, so this is not a scientific
PASS or FAIL. The new A02 successor allocation is in the adjacent `t0b` package;
it does not overwrite or relabel this STOP.
