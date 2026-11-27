# R11 result: capture dimensions blocked input

Date: 2026-11-23 (Asia/Tokyo)

## Outcome

**STOP_SETUP in all four planned combinations.** The standard-Python and
optimized runs each started the two isolated cases and successfully found the
visible Edge window through its unique profile process ancestry. The first
screen observation then stopped before handle mint or task input because
Chromium CDP capture returned 756×457 pixels while `Win32Backend.geometry`
reported a 756×488 client area. R10's window discovery problem is therefore
resolved, but the mismatched screenshot coordinate frame prevents safe input.

Each raw case has zero minted handles, admissions, native operations and POSTs.
The backend's empty final release receipt is verified, each unique profile was
removed, and the prior foreground window was restored. No task button state
was claimed: before focus/input the final `GetAsyncKeyState` evidence is
unknown. Edge was `157.0.4341.60`. One standard-mode fixture server logged a
client connection reset during browser shutdown; this did not dispatch input
or alter the setup stop. There were no model/provider calls.

## Interpretation

R11 does not establish native input, release after task action, task success,
or generation-change refusal. The title/PID and profile-ancestry checks work.
The remaining setup mismatch is between a CDP page screenshot and the native
client frame. R12 will source point minting and OCR from the Win32 backend's
own window-client capture, and will retain CDP only for page loader metadata,
navigation and controlled reload.

## Frozen artifacts

- Protocol: [PROTOCOL.md](PROTOCOL.md)
- Harness and protocol freeze: commit `ea8ebfb8a88c0de592728e6a43db3c6a7c59b45b`
- Standard and optimized raw cases: [raw](raw)
- Raw SHA-256 manifest: [SHA256SUMS.json](SHA256SUMS.json)
