# Win32 supervised standard-caller R26 — supported maximum response wait

R24's one action completed and released after its 8 s public wait returned
pending. R25 tested a fresh generation but the caller rejected a 12 s wait
before input with `INVALID_RESPONSE_WAIT`. The implementation accepts waits up
to 10,000 ms. R26 uses that supported maximum with a third fresh fixture,
generation, supervised stdio-MCP session, program, lease, and sentinel.

The input-free preflight verifies the exact R24 action/effect/release receipts
and the exact R25 no-input refusal, including their raw and audit hashes. The
probe uses the public observe/validate/dispatch path once, waits no more than
10 seconds for the terminal result, records the release receipt's own monotonic
timestamp, checks the fixture's effect file and exact event journal, and then
closes the session and owned fixture. No WSLc or Docker, replay, retry,
cancellation, external window, or fallback input is used.

PASS requires a terminal completed dispatch, verified all-up release, exact
independent effect, public session close, clean fixture exit, and restoration
of the previous foreground window. Runtime `task_success` must remain null.
