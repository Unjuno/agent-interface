# Supervised Win32 standard-caller trial R03

R03 is a fresh, one-shot native Windows fixture trial of the public stdio MCP
`--session-mode supervised-win32` route. R01 found a producer/call-directory
collision, repaired in `5da333c6bfc43dea34c82b251b2281aead254ed3`. R02 then
passed its narrow integration question but exposed a null `input_dispatched`
summary despite accepted native emissions and an independently saved effect.
Commit `a448064ec27fcc67b8da6663cb9f01a646629039` adds the backend-emission
fallback and a regression test using the native result shape.

R03 uses a new task string and lease ID. Its one public dispatch waits up to
30 seconds for a terminal response, then the probe retrieves only that same
call if needed. The frozen audit requires `status=returned`,
`operation_invoked=true`, and `input_dispatched=true` in the retained standard
report, alongside verified empty release state, same-operation/generation
neutral readback, exact independent fixture effect and journal, and clean
fixture/session shutdown. The probe retains timing around observation,
validation, dispatch, each result readback, and close.

The condition packet freezes the source commit, exact task, operations,
timeouts and fail/unknown rule. `conditions.json`, `README.md`, `probe.py`, and
`audit.py` are bound by `SHA256SUMS.freeze` before fixture creation. The attempt
may run once; `raw.json`, `audit.json`, and `SHA256SUMS` are preserved afterwards.

This trial does not test cancellation or blocked-I/O recovery. It does not
establish an atomic generation fence, a hard physical release deadline, MAP01,
runtime-integrated task success, matched efficiency, or broad reliability. It
uses no WSLc or Docker allocation.
