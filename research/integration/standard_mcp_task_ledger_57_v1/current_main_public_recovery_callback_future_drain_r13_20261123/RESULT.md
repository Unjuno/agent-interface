# R13 result: direct public observation Future drain

**Disposition: PASS for the narrow direct-observe harness case.** One fresh normal and one fresh `-O` run both exited 0 and reported one test `OK`. The 8-second caller-side Future wait timed out while the observation remained in flight; the test released and awaited that same Future, verified one callback, a finalized exact-call report with no temp file, and no input dispatch before teardown. Runtime was 44.108 seconds normal and 46.170 seconds optimized, showing substantial scheduling/host delay despite the small callback body.

This is a deterministic Fake-only direct MCP observation diagnostic. It does not exercise the compiled caller, recovery/task effect, live Win32 input, MAP01, efficiency, Research Preview, or runtime distribution. It does not validate the R04/R09/R10 lifecycle cohorts or explain R10's native invalid-HWND orphan.

## Source audit note for R10 anomaly

In `runtime/cli_v1/mcp_server.py`, `submit()` accepts work through `loop.run_in_executor(None, ..., invoke, ...)`, while the supervised observe branch calls the module-global `observe` from inside `invoke`. The observer callable is therefore resolved when the worker reaches that branch, not captured at API admission. The R10 callback Future remained incomplete after its 8-second wait and close stayed busy through a 30-second drain. A queued or late worker reaching the global after a test patch scope unwound is a plausible explanation for the real invalid-HWND observation. The retained R10 artifacts do not prove this sequence; keep the cause unresolved and do not restore Fake-only attribution to R04/R09/R10.

R13 raw logs, exact exit codes, conditions, source hash, and packet manifest are retained alongside this result.
