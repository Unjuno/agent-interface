# #1113 first allocation stop

Disposition: `STOPPED_OUTER_EXECUTION_TIMEOUT`.

The source-first Rung1 allocation was frozen and ownership-clean. Exactly one formal runner invocation was launched from the frozen source. The external container execution ceiling stopped the process before `FORMAL_RESULT.json` was written. Post-stop inspection found no surviving runner/fixture process, no formal result and no audit file. `TIME.txt` was created but remained empty.

This is an orchestration/transport stop, not a scientific PASS/HOLD/FAIL. The primary seed is consumed for this allocation and is never rerun. Construction-only IPC observations remain nonformal and are not pooled.

A separately versioned successor may preserve the exact scientific contract and change only outer execution transport to one detached supervisor process polled to completion. It must use fresh task/case identities and must not pool #1113 rows.
