# Current-main Win32 public-caller fixture replication R04

Status: `PASS_SCOPED_REPEAT`; this is a second consecutive fresh fixture success after the receipt-capacity fix.

- Source main `c2e8787eb7e965d44315974f668a10ad8b1395b0`.
- Fresh PID 35052 / HWND 17828402. Computer Use raised that exact window; foreground check matched its PID/HWND/title before dispatch.
- One public standard `supervised-win32` program: focus, one A key chord, release_all. No provider/model call and no retry.
- Action `f087c4d6497d4bb6a75c01172273c128`, call `7f8dae289eae480b988ce47c4ebb0d00`: completed, release-confirmed true, task_success null, replay false. All three operation receipt phases were completed; key chord had two returned SendInput calls.
- Release receipt verified and returned the A key-up with no held/unknown key/button state.
- Completion custody sampled the 2 s late-input horizon 77 times; largest observed gap 32 ms against 100 ms maximum; no late-input validation error.
- Independent fixture event log received A keydown and keyup, then recorded verified `text="a"` after 6 s. This application effect is later than the runtime completion observation window.
- Recovery was not required. The exact run-owned fixture was closed with Computer Use Alt+F4 and is absent from UI inventory and process lookup.

This is only a second scripted fixture sample. It does not establish MAP01, provider/model efficiency, a reliability rate, or Research Preview graduation. See `raw/`, `conditions.json`, and `SHA256SUMS`.
