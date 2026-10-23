# Valid-generation public Win32 MCP effect trial R03

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

This is a distinct one-shot attempt after R01's import-path and R02's invalid
backend-close failures. Both earlier attempts are preserved in their own
packets and will not be rerun or overwritten.

`conditions.json`, `probe.py`, `audit.py`, and this README were committed before
the trial. After the one-shot run, its raw result, audit, and SHA-256 inventory
will be committed in a separate evidence commit. The result will be scoped to
this fixture and this sample; it cannot establish atomic HWND lifetime
protection, the post-focus foreground race, hard release deadlines, blocked
I/O recovery, MAP01, efficiency, or broad reliability. No WSLc or Docker
allocation is used.

## Frozen R03 outcome

The public path reached a real input attempt: the public observation returned a
matched generation, static validation accepted, the single standard dispatch
completed, and its release receipt was verified with no keys or buttons down.
The owned fixture independently journaled the text and save event, wrote
`{"clicked":false,"saved":true,"text":"PUBLIC-MCP-OK-9C17"}`, and exited 0
after its window was closed. However, the frozen `operations` text is
`PUBLIC-MCP-OK-9C17` while the separately frozen `text_effect` acceptance field
is `PUBLIC-MCP-OK-E5F0`. The probe and audit therefore score
`FAIL_OR_UNKNOWN` (11/13 audit checks); the mismatch invalidates the predeclared
acceptance condition. No retry was made. `raw.json`, `audit.json`, the public
responses, call reports and artifact are retained under `run/` and covered by
`SHA256SUMS`. R04 will add a pre-run consistency guard in its own packet.

