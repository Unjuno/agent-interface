# Supervised Win32 standard-caller trial R04

R04 is a fresh, one-shot native Windows fixture trial of the public stdio MCP
`--session-mode supervised-win32` route. R01 found and repaired a producer
directory collision in commit `5da333c6bfc43dea34c82b251b2281aead254ed3`.
R02 then passed its narrow integration question and exposed a missing
`input_dispatched` summary, repaired with a native-shaped regression test in
commit `a448064ec27fcc67b8da6663cb9f01a646629039`. R03's frozen preflight was
rejected because it requested a 30000 ms wait above the public caller's
10000 ms maximum; its raw records no call ID and no input, and it is preserved.

R04 uses a new task string and lease ID, and sets `wait_for_result_ms=10000`.
The initial dispatch may return pending or completed. The frozen audit then
requires the retained report and terminal readback for that exact call to show
`status=returned`, `operation_invoked=true`, and `input_dispatched=true`. It
also checks same-operation/generation verified empty release, later independent
neutral readback, exact fixture effect and event journal, and clean fixture and
session close. Timing is retained around observation, validation, dispatch,
each result readback, and close.

The condition packet freezes the source commit, task, operations, timeouts and
fail/unknown rule. `conditions.json`, `README.md`, `probe.py`, and `audit.py` are
bound by `SHA256SUMS.freeze` before fixture creation. The attempt may run once;
raw output, audit and final hashes are preserved afterwards.

This trial does not test cancellation or blocked-I/O recovery. It does not
establish an atomic generation fence, a hard physical release deadline, MAP01,
runtime-integrated task success, matched efficiency, or broad reliability. It
uses no WSLc or Docker allocation.
