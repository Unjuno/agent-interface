# #1893 typed claim-sink cut-set transfer — retained formal stop

Decision: **`STOP_FORMAL_HARNESS_MUTATION_INVALID`**. Scientific result: **NONE**.

The source-first frozen analyzer was invoked once. Before any RESULT could be produced, the `recovered_before_recovery` corruption generator moved the only statement out of the candidate `if` body. Parsing that intentionally corrupted control therefore raised `IndentationError` instead of returning a clean rejected-mutation verdict.

This is a harness failure, not evidence for or against the typed-sink hypotheses.

- formal invocations: 1
- reruns/replacements/tuning: 0
- X11/live reruns: 0
- frozen source changed after formal: no
- elapsed to stop: 0.65 s; max RSS 94,632 KiB

The byte-pinned #827 files remain exact:
- watchdog.py blob `8bfacbdd2ba46e1433e79c3144e1c754c058ec8c`;
- run_case.py blob `9a9730ad38bbcc83714a97e66f3597785b646693`;
- run_case_a2.py blob `3d4933020a9e2ef68ba5c3bcd85c5d74a19e44c5`.

The transport mismatch discovered before formal is separately retained in SOURCE_FREEZE and had zero scientific rows. It was repaired and read back exactly before this invocation.

A successor may repair only the corruption-control harness, use a fresh task/path/branch, preserve the pinned source identities and the five preregistered scientific classifications, and must not pool or rerun #1893.
