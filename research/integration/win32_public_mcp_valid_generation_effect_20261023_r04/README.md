# Valid-generation public Win32 MCP effect trial R04

This is a one-shot native Windows experiment on a user-authorized local PC.
It targets only a fresh `runtime.backends.win32_v1.fixture_app` process owned
by the probe. The public stdio MCP caller first observes that process, then
validates and dispatches one program carrying the generation token from that
observation. The program types a fixed sentinel into the fixture, invokes the
fixture's local save action, and ends with `release_all`.

The probe refuses to overwrite `run/` or `raw.json`; it requires the exact
source commit in `conditions.json`. It makes one public validation and one
dispatch, preserves all returned content and child logs, and closes only its
owned fixture. It does not retry or replay. The independent effect file and
event journal provide the task result; a dispatch receipt alone is not scored
as task success. `audit.py` is frozen before execution and reads retained raw
only.

This is a distinct one-shot attempt after R01's import-path failure, R02's
invalid backend-close failure, and R03's frozen operation/effect mismatch.
Those earlier attempts remain preserved in their own packets and will not be
rerun or overwritten. R04 checks the frozen text-effect condition against the
operation before creating the fixture, and the independent audit checks that
same condition again.

`conditions.json`, `probe.py`, `audit.py`, and this README were committed before
the trial. After the one-shot run, its raw result, audit, and SHA-256 inventory
will be committed in a separate evidence commit. The result will be scoped to
this fixture and this sample; it cannot establish atomic HWND lifetime
protection, the post-focus foreground race, hard release deadlines, blocked
I/O recovery, MAP01, efficiency, or broad reliability. No WSLc or Docker
allocation is used.

## Frozen R04 outcome

R04 passed all 14 frozen audit checks. Public `interface_observe` returned a
matched target generation, identical to the independent native identity for
the owned fixture. Public static validation accepted the exact frozen program,
and its one standard dispatch completed. The final `release_all` receipt was
verified with empty `keys_down`, `buttons_down`, `keys_unknown`, and
`buttons_unknown`. The independent fixture effect file recorded
`{"clicked":false,"saved":true,"text":"PUBLIC-MCP-OK-B741"}`; its event journal
contains `ready`, all 18 expected WM_CHAR records, and one save event. The
fixture closed with exit code 0 and its HWND no longer existed. The full raw
MCP responses, call reports, capture, fixture records, and 14-check audit are
retained below `run/` and in `raw.json`/`audit.json`; `SHA256SUMS` covers them.

This is one owned-fixture sample of accepted input, verified release, and
independent task-effect readback through the public stdio-MCP caller. R01 and
R02 were setup failures. R03 emitted the same kind of effect but its frozen
expected string disagreed with its frozen operation and remains an audit
failure. None of these samples establish a hard release deadline, the
post-focus foreground race, blocked-I/O recovery, MAP01, efficiency, or broad
reliability.

