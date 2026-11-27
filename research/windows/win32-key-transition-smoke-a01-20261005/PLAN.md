# Win32 key transition host smoke A01

## H / T / D / C / U

**H.** On this Windows host, the backend's real `SendInput` acknowledgements and `GetAsyncKeyState` samples may form a matched DOWN/UP state-change window while a dedicated window owned by the probe process is foreground.

**T.** Instantiate the repository's `Win32Backend` with a tiny built-in `STATIC` window created by the same process. Require that this HWND is foreground and left Shift is initially up before sending one Shift DOWN and one Shift UP. Attempt to restore the prior foreground window and destroy the probe window in `finally`; if preconditions fail, send no key input. Record API receipts and the final state only.

**D.** Scoped PASS requires one explicit DOWN and one explicit UP receipt with the same owned hold ID and backend instance, acknowledged `SendInput` calls, sampled down then up state, and `release_all()` verified neutral. A cleanup UP may also be recorded because the backend retains the explicit-UP obligation until terminal neutral verification; if present, it must be separately marked `cleanup=true` and its post-sample must be up. Any failed precondition is a STOP; any API or assertion failure is a retained failure.

**C.** This is one controlled direct-backend native-API smoke on one Windows session, with a process-owned foreground target. The program/step labels are test context set by the probe; core admission and `Win32RuntimeSession.dispatch()` are not exercised. Timestamps are retained as returned by this host; equal timestamp values do not establish zero latency.

**U.** No physical keyboard hardware state, app consumption, secure desktop/UIPI, elevated target, DPI behavior, task effect, latency claim, game/MAP01 outcome, or Issue #59 completion is established. Synthetic input reaches the Windows input path; it is not a physical-keyboard action.
