# Valid-generation public Win32 MCP effect trial R02

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

This is a distinct one-shot attempt after R01's pre-MCP import-path failure.
R01 remains preserved in its own packet and will not be rerun or overwritten.

`conditions.json`, `probe.py`, `audit.py`, and this README were committed before
the trial. After the one-shot run, its raw result, audit, and SHA-256 inventory
will be committed in a separate evidence commit. The result will be scoped to
this fixture and this sample; it cannot establish atomic HWND lifetime
protection, the post-focus foreground race, hard release deadlines, blocked
I/O recovery, MAP01, efficiency, or broad reliability. No WSLc or Docker
allocation is used.

## Frozen R02 outcome

R02 is `FAIL_OR_UNKNOWN` (3/13 frozen audit checks). The repository import
path worked, and the probe verified that the fixture HWND belonged to its
owned process and generated a valid native identity. It then raised
`AttributeError` because `Win32Backend` has no `close()` method. No MCP
observation, validation, or dispatch ran; the fixture journal contains only
`ready`, no effect file exists, and the owned window/process closed cleanly.
No input was emitted and this frozen attempt was not retried. `raw.json`,
`audit.json`, and `run/` retain the result. R03 removes that invalid close call
in a separate frozen one-shot attempt.
