# Valid-generation public Win32 MCP effect trial R01

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

`conditions.json`, `probe.py`, `audit.py`, and this README were committed before
the trial. After the one-shot run, its raw result, audit, and SHA-256 inventory
will be committed in a separate evidence commit. The result will be scoped to
this fixture and this sample; it cannot establish atomic HWND lifetime
protection, the post-focus foreground race, hard release deadlines, blocked
I/O recovery, MAP01, efficiency, or broad reliability. No WSLc or Docker
allocation is used.

## Frozen R01 outcome

R01 is `FAIL_OR_UNKNOWN` (4/13 frozen audit checks). The probe launched its
owned fixture, then failed while importing `runtime.backends.win32_v1.backend`
because the probe's script directory, rather than the repository root, was on
`sys.path`. It made zero MCP validation/dispatch calls. The independent fixture
journal contains only its `ready` event, no effect file exists, and the probe
posted `WM_CLOSE`; the process exited 0 and the HWND was destroyed. No input was
emitted. This frozen attempt was not retried. `raw.json`, `audit.json`, and
`run/` preserve the failure and clean shutdown; `SHA256SUMS` covers the packet.
R02 is a separate future attempt with a corrected frozen import path.
