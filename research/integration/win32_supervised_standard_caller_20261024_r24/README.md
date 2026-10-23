# Win32 supervised standard-caller R24 — fresh generation after recovery

## Question

After R23 recovered and closed a supervised Win32 session, can a distinct new
fixture generation in a new supervised stdio-MCP session accept one fresh
observation-bound action, complete an independently scored task effect, and
close with verified all-up input?

R23 is the predecessor, not a replay: its immutable raw packet records one
recovered cancellation, a same-generation independent Q-up readback, a clean
session close and fixture exit, then a fail-closed refusal of another action on
the same generation. R24 uses a new fixture process, new target map, new MCP
process/session, new observation, lease, program ID, and sentinel.

R23's current-main raw blob hash is `e4106c26a078dd57a1379e456506f983b1fa5761ed7f00168b145b961807ea5f`,
while its final manifest and follow-up audit claim `b46e11d7abc460cf1160960fbf683462f0a5c9bb13bffac33f0844e8f3becda8`.
R24 preflight records this discrepancy and separately checks the recovery,
release, Q-up, fail-closed, effect, and cleanup fields in the actual raw bytes.
It does not revise the preserved R23 audit or outcome.

## Frozen method

The probe starts one owned `runtime.backends.win32_v1.fixture_app` window and
configures the standard public `runtime.cli_v1.mcp_server` stdio caller in
`supervised-win32` mode for only that HWND. It obtains a public observation,
checks that its target generation equals the independent Win32 binding and
differs from R23, validates one finite click/text/save/observe/release program,
and dispatches once. It then reads the fixture effect file and event journal,
checks the retained public release receipt, closes the interface session and
fixture, and restores the previously foreground window when it still exists.

The frozen PASS gate requires R23's predecessor recovery and cleanup receipts,
a distinct new generation, a matching public observation, one completed public
dispatch, exact independent task effect and event counts, verified all-up
release, `task_success=null`, closed session, clean fixture exit, and successful
foreground restoration. Any uncertain result remains preserved; no retry,
cancel, replay, fallback input, WSLc, or Docker operation is allowed.

## Limits

R24 is a new task attempt after R23, not an uninterrupted transaction spanning
the earlier recovery. It can show that a fresh supervised session on a distinct
generation performs an independently scored action after the predecessor
session closed. It cannot establish same-session continuation, release under
blocked native I/O, atomic capture-to-input fencing, runtime-integrated task
success, MAP01, WSLc transfer, matched efficiency, or broad reliability.
