# Win32 native SendInput recovery results

R04 is a one-PC, owned-fixture qualification sample against runtime source `0aceb89d2cebcd7fe3f052a76b30782b12df3154`. It used only CTRL and fresh `fixture_app` windows. The two pauses were before the real SendInput call and after SendInput returned one accepted event; neither pauses inside the Windows API/kernel call.

| Attempt | Raw | Independent audit | Spawn preflight |
|---|---|---:|---:|
| win32-native-sendinput-recovery-20261023-r01 | FAIL_OR_UNKNOWN | FAIL_OR_UNKNOWN (2/6) | not applicable |
| win32-native-sendinput-recovery-20261023-r02 | FAIL_OR_UNKNOWN | FAIL_OR_UNKNOWN (5/12) | PASS |
| win32-native-sendinput-recovery-20261023-r03 | PASS | FAIL_OR_UNKNOWN (15/17) | PASS |
| win32-native-sendinput-recovery-20261023-r04 | PASS | PASS (17/17) | PASS |

R01 preserved the spawn-import output-guard failure before either input schedule. R02 preserved a runner wait-state error in the first schedule; no CTRL-down was sent. R03 completed both schedules and the task effect, but its frozen audit required strict timestamp inequality and rejected tied millisecond-resolution timestamps. R04 records producer-join then recovery-claim using an ordered same-process event sequence and matches the recovery ID received by the helper; its frozen audit passes 17/17.

R04 observed terminal recovery at 1515 ms and 1531 ms from cancellation, under the frozen 8000 ms terminal bound. Each observer sampled for at least 1500 ms and found CTRL-up on every sample with the same target generation, foreground HWND, and active input-desktop witness. The fresh public stdio-MCP task saved the exact expected text and event journal; its verified release receipt contained no down or unknown keys/buttons. All runner-owned fixtures exited with their windows gone, and the raw cleanup error list is empty.

This is a narrowly scoped positive sample, not a hard-real-time guarantee, blocked-inside-SendInput test, MAP01 qualification, WSLc portability result, efficiency comparison, or broad reliability claim. No WSLc or Docker command was run. R01–R03 failures and audit outcomes remain unchanged.
