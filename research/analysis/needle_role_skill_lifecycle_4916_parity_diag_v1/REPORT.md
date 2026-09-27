# Issue #5053 scorer-parity diagnostic

The one-shot frozen OrbStack Docker construction diagnostic passed: all
12,288 retained seed-3788 predictions match after transposing the saved
rank-by-output LoRA matrix B before the row-major linear helper. The frozen
candidate suite exited 0, and the separate raw-only auditor independently
recomputed all 12,288 predictions with zero mismatches and verified 8/8
receipt/hash/test controls.

The defect was an orientation mismatch: saved B is 2x4 for `h @ a @ b`, while
the earlier candidate helper expects output-by-input rows (4x2). Passing B
without transposition produced only two adapter deltas and discarded classes.
The predecessor scorer and its first-rung STOP artifact were not altered.

This is implementation-parity evidence only. No lifecycle timing was run in
this allocation. See `FREEZE.json`, `results/diag-01/`, and Issue #5053 for the
preregistration, raw receipts, independent audit, exact hashes and limitations.
