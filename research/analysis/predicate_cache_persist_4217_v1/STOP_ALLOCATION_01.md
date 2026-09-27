# Allocation 01 STOP

Allocation: `predicate-cache-persist-4217-20260923-01`

Disposition: `STOP_EXTERNAL_EXECUTION_TIMEOUT`; scientific rows 0; scientific verdict NONE.

The one frozen `python -B run.py` invocation exceeded the surrounding 30 s execution-tool envelope before stdout, parent exit receipt, or `FORMAL.json` was retained. Post-timeout read-only inspection found no live study process, empty captured stdout/stderr, absent FORMAL.json and absent RUN_EXIT.txt. The consumed allocation is not rerun.

This is an execution-envelope failure, not a scientific predicate-cache outcome. The source-first public freeze remains immutable. Allocation 02 changes only orchestration granularity and Python site startup (`-S`), not candidate, cases, policy semantics, audit gates or scientific denominator.
