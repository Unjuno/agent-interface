# R04 result: PASS for the frozen narrow question

The frozen audit passed 15/15 checks. Public observation's target generation
matched the owned fixture HWND; static validation passed. One public dispatch
returned `pending` after 10002.794 ms. Fifteen read-only result calls retrieved
the same call as `returned` with `operation_invoked=true`,
`input_dispatched=true`, and a completed action. This verifies the R02 caller
summary repair on the native backend result shape.

The action's execution reported 70 accepted emissions over a 31 ms interval.
The producer exit was confirmed 125 ms after execution start. Its verified
release receipt had no down or unknown keys/buttons, and an independent neutral
readback for the same operation and target generation ran after exit detection.
Both monotonic timestamps rounded to the same value, so this sample provides
ordering evidence but no positive measured exit-to-readback delay. The fixture
journal contains the exact click, all characters of
`SUPERVISED-MCP-OK-20261024-R04`, and one save event; the separately read effect
file matches the frozen expectation. The fixture exited cleanly, the old
foreground window was restored, the supervised session closed, and runtime
task success remained `null`.

This establishes one successful standard-MCP path through generation
forwarding, task effect, input release and independent neutral observation. It
does not establish cancellation or recovery under blocked I/O, a hard release
deadline, atomic generation fencing, MAP01, runtime-integrated task success,
matched efficiency, or broad reliability. No WSLc or Docker allocation was
used.
