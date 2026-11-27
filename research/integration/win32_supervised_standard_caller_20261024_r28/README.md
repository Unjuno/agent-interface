# Win32 supervised standard-caller R28 — independent exact-call retrieval repeat

## Question

Does the R27 pending-result retrieval behavior repeat once on a fresh fixture and the current integrated main commit? R28 fixes source commit and runtime source hashes to the post-#9470 main tree, uses a new target generation/session/program/sentinel, and permits exactly one dispatch. If dispatch returns pending, the only follow-up is read-only `interface_results` for that exact call ID, every 200 ms for at most 15 seconds.

R27 is the direct predecessor and must retain its immutable strict audit PASS, exact-call completed result, independent effect, release receipt, cleanup, and foreground restoration. R25 remains a separate input-free refusal control. The preflight checks both before any fixture or input starts.

## Frozen decision

PASS requires pending dispatch, terminal completed result for the same call ID within the retrieval bound, verified all-up release, producer exit and neutral same-generation readback, the exact independent effect and event journal, successful session and fixture close, foreground restoration, and runtime `task_success=null`. Otherwise preserve `FAIL_OR_UNKNOWN`; never redispatch.

## Scope

One local native Windows fixture only. This does not establish WSLc, blocked-I/O release, MAP01, integrated task success, matched efficiency, or broad reliability. R27 remains unchanged.
