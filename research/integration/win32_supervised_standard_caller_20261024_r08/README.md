# Win32 supervised standard MCP cancellation and recovery — R08

R08 is one new frozen live attempt through the public stdio MCP caller. The previous R07 trial observed the native Q-down 45.7678 seconds after a zero-wait dispatch response, just beyond its 45-second hook wait. R08 extends that finite wait to 75 seconds and the one-use program lease to 150 seconds.

The probe receives the dispatch call ID first, waits for the owned hook to confirm the injected Q-down, reads `interface_results` to confirm that exact action is still running, and calls `interface_cancel` once. The hook holds Q-down for at most 1.5 seconds and the runner releases it immediately after cancellation returns. Evidence includes exact producer identity and exit, hook-observed recovery Q-up, a fresh-process same-generation Q-state readback, the independent fixture save sentinel, and full cleanup.

PASS requires same-operation recovery after producer exit, independent neutral readback within 2500 ms, exact effect, and cleanup. Any mismatch or timeout is preserved as FAIL_OR_UNKNOWN without replay. The packet and source hashes are frozen before its sole run. No WSLc or Docker allocation is used.
