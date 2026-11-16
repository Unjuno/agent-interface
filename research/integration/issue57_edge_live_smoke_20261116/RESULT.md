# Result

Invocation 1 failed before input because the sparse checkout omitted the
Windows OCR worker. Invocation 2 used the exact tracked worker file from the
pinned main source. The one-time Edge run reached all task assertions: the
caller reported `TASK_SUCCEEDED`, the local independent HTTP oracle accepted
exactly one expected-value POST, the compiled receipt reported one completed
transition with verified release, and frontier-model resumptions were zero.

The test then failed during `TemporaryDirectory` teardown with `WinError 32`
because `profile/Default/Collections/collectionsSQLite` remained locked. The
overall test is therefore **ERROR**, while the task-effect assertions passed.
No input was retried. Read-only process inspection found no current Edge
command line matching the exact temporary profile; no process was stopped and
the retained temporary profile was not manually removed. A deletion command
after verifying the exact workspace-contained path and absence of a matching
Edge command line was rejected by execution policy; it was not bypassed.

This is one live local Edge effect using an offline test double. It supplies no
provider accounting, no comparative arm, no full raw HTTP/capture archive, no
Calc effect, and no MAP01 result. It does not satisfy Issue #57's integrated
efficiency milestone. Fix and verify bounded browser cleanup before another
run; preserve this attempt as-is.
