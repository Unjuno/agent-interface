# R01 result: FAIL_OR_UNKNOWN

The frozen audit scored 7/14 checks. Public observation returned a target
generation matching the owned fixture, static validation passed, and cleanup
closed the fixture with exit code 0 and restored the prior foreground window.
The dispatch did not emit input: its retained report says
`invalid_request / unknown caller action or producer`, with
`operation_invoked=false` and `input_dispatched=false`. The owner result retained
the operation as `unknown` with a Windows `FileExistsError`; the fixture journal
contains only its initial `ready` event, and no effect file was written.
`interface_close` returned `busy`, preserving the unresolved operation and
`release_confirmed=false`. The packet and result are not retried.

Source tracing identified a deterministic path collision. The MCP caller first
creates `calls/<call_id>` for its request and report. The native producer factory
was given the same root and also created `<root>/<call_id>` with
`exist_ok=false`. Thus producer registration failed before its gated process
could execute. A new regression test reproduced this collision before repair.
The repair assigns native producer directories to the separate
`supervised-win32-producers/<call_id>` namespace in commit `5da333c`; its
regression test and related local suites pass after the change. R02 is a fresh
one-shot attempt against that commit and is recorded in the sibling packet.

R01 establishes no task effect, completed release, neutral readback, successful
session close, blocked-I/O release, recovery bound, atomic target fence, MAP01,
efficiency, or reliability claim. Its raw and frozen audit remain immutable.
