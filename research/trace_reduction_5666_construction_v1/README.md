# #5666 host-only construction check

This is an additive, synthetic method construction for [Issue #5666](https://github.com/Unjuno/agent-interface/issues/5666). It is **not** a formal allocation, a container result, an independent audit, a replay of a retained failure, or a GUI safety result.

Run: `python research/trace_reduction_5666_construction_v1/check.py` with Python 3.12 (standard library). The script asserts that a six-node toy trace can remove irrelevant `noise` while preserving a frozen typed wrong-target fingerprint; deletion of grant or release produces a different failure despite exit code 1. It checks one-node minimality only under its tiny declared grammar.

The first local construction invocation exited 1 due to a bug in the test: after removing `noise`, the check attempted to remove that already-absent node and therefore compared the trace with itself. The check was repaired to enumerate all remaining nodes; the second host invocation exited 0. This is a construction-code repair, not a retry of a formal allocation. The original failure is recorded on the Issue and in REPORT.md, not represented as a scientific negative result.

No method PASS is claimed. T0 remains `HOLD_NO_REPLAYABLE_FAILURE`; a real test needs #1715-style replay fidelity, exact setup restoration, independent scorer, and an allocated isolated runtime.