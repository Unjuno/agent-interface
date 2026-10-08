# Recovery status — 2026-10-01

This source-only recovery preserves the exact frozen experiment package from
the original #4340 branch. The branch head contains no formal timing batches,
raw receipts, audit output, or controls output; formal executions remain 0.

The frozen target is Linux x86_64 / CPython 3.13.5 / NumPy 2.3.5 on a named
AMD EPYC host with CPU affinity. The available validation host is macOS arm64
/ CPython 3.14.5, so it is not a valid substitute for the frozen performance
environment. No timing experiment was started. Local construction checks only:
8/8 unit tests pass and nine Python files syntax-compile; these do not validate
the frozen timing hypothesis.

The original source/freeze paths are preserved byte-for-byte. No formal result
is claimed, no environment substitution or rerun occurred, and no runtime
promotion is implied. Formal execution remains pending the exact frozen
environment and its predeclared gates.
