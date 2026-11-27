# R44 OS-pipe recovery attempt

Classification: `FAIL_OR_UNKNOWN_FIRST_OUTCOME_RETAINED`; scoped cancellation recovery was later confirmed. R41–R43 first outcomes remain immutable.

## Question

Can the standard public stdio relay route cancellation and bounded Win32 recovery while the actual child-process stdout OS pipe is full and a write is blocked?

## R44 runner change

R44 preserves R43's failure-path public cancellation, exact-call result polling, close receipt, and no-replay custody. It repairs the R43 setup defect by passing `create_server`'s distinct request-journal root and producer root through paired owner and producer factories. The source freeze includes `owned_win32_session.py`.

## First outcome

Fresh fixture, foreground, target-generation and public observation preflight passed. `interface_dispatch` returned queued; no independent SHIFT-down was seen during the 3-second admission window, so pressure was not applied. Failure-path standard `interface_cancel` returned pending. Polling the exact call first showed the action running with cancellation pending, then recovered. The cancellation record confirms producer exit `-15`, `release_confirmed=true`, and recovery completion 47 ms after cancellation was requested. A later same-generation native readback found SHIFT up. `interface_close` returned closed with zero unresolved calls, the fixture exited 0, and the original foreground HWND was restored exactly. Runtime task success remains null, as expected for a cancellation.

This is a scoped post-start cancellation/recovery sample, not release under blocked OS-pipe output: the down state was never independently observed and the full-pipe/outstanding-write gate was not reached. The source manifest verifies 12/12 entries and raw manifest 19/19. The additive auditor reports no mismatches. No WSLc or Docker operation occurred; no replay.

The run demonstrates the repaired harness's failure-path custody sequence and an actual public cancellation recovery. Its MCP server adapter remains in-process even though relay child stdout is a real OS pipe. It is not a production MCP subprocess transport, MAP01, a task-effect result, matched efficiency, or a reliability estimate.

## Status and limits

This packet is an additive successor; it does not revise R41–R43.
