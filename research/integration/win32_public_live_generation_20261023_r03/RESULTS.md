# Public live HWND-generation test results

R03 is the preregistered result against current-main runtime source `8f4aa65163dee86024371f8ad1e46888ef04de2f`. It exercised the registered `guarded-win32` create-server tool handlers with live Win32 HWND/PID/thread/process-generation reads; input dispatch was intentionally impossible because the producer factory only recorded and rejected calls.

| Attempt | Registration | Raw | Audit | Key disposition |
|---|---|---|---|---|
| win32-public-live-generation-20261023-r01 | exploratory, after-run freeze | FAIL_OR_UNKNOWN | not run | generation changed; producer calls 0 |
| win32-public-live-generation-20261023-r02 | frozen before run | FAIL_OR_UNKNOWN | FAIL_OR_UNKNOWN (6/8) | expected refusal observed; assertion/read-path extraction was wrong |
| win32-public-live-generation-20261023-r03 | frozen before run | PASS | PASS (8/8) | UNKNOWN before producer factory; no input |

For R03, both real target-generation digests are valid and differ. Bind and admission retain Generation A; after the injected live-target reader moves to Generation B, the registered start tool returns UNKNOWN with `target_generation_changed_before_start`. `interface_results` retains that action state; the operation owner remains UNKNOWN with its gate closed, no producer identity, no release claim, no task success and replay denied. The producer factory call list is empty.

All R03 fixture processes exited with code 0 and their HWNDs were gone; cleanup errors are empty. The test uses in-process `server.call_tool`, not stdio transport, and emits no input. R01 and R02 raw and audit outcomes remain unchanged.

This result narrows the live target-generation boundary through the standard caller before producer start. It does not join a native input producer or recovery adapter, prove atomic HWND fencing, validate task effects, test blocked SendInput recovery, qualify MAP01 or WSLc, or establish efficiency or reliability.
