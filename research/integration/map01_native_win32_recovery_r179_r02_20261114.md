# MAP01 native Win32 recovery R179-R02 (2026-11-14)

## Classification

`PARTIAL_EVIDENCE_STRICT_PREREGISTRATION_FAIL`. The trial performed one native LEFTDOWN and did not replay it. Its public terminal record preserves the source action as `unknown`, `release_confirmed=false`, `task_success=null`, and `replay_allowed=false`; a separate cancellation result says `recovered` and `release_confirmed=true`. The runner stopped at its conservative top-level projection assertion before its own post-stop checks completed.

The retained terminal shape explains the assertion: the query envelope has `input_dispatched=false` and no `release_confirmed` value; the nested source action has `input_dispatched=true` and `release_confirmed=false`; the cancellation is a separate recovered result. Do not promote cancellation release evidence to the source action or treat the harness assertion as a passing attempt.

## Evidence

- Frozen source: `06450f80e4e9b36ac1bbe604550e99380cbc98aa` (tree `1382c11ef45a23fb5d7d235bfbe3f3f946b0a9c8`).
- Attempt: `map01-native-auto-completion-recovery-r179-r02-20261114`; one accepted Win32 LEFTDOWN, producer exited 86, cancellation reported automatic recovery, replay denied.
- Cancellation record: 2,000,000,000 ns late-input interval, 78 observations, maximum observed gap 32 ms, and same-generation neutral readback. Its strict `late_input_horizon_verified` field is absent and `recovery_release_key_up_attempts` is empty.
- After the runner stopped, an independent read-only horizon verified 2 seconds of LEFT/W-up with the same process identity and target generation (176 samples, maximum sample gap 13.3955 ms). This is post-stop evidence and does not repair the strict runner failure.
- A public `interface_observe` call returned with matched generation. Its screen capture was occluded by another window in the registered ammo ROI; the preregistered classifier returned UNKNOWN (all four template distances 1.0). A second `window_client`/PrintWindow capture was black and also UNKNOWN. A partial visible HUD strip showed 49, but neither capture qualifies the preregistered effect oracle. The exact 50→49 effect therefore remains unverified; `task_success` remains null.
- One bounded exact-owned WM_CLOSE request was attempted after verifying the neutral horizon and process/HWND/generation binding. The wait reached a signaled process handle, then the helper failed while retrieving the exit code because the auxiliary ctypes prototype was not configured. A subsequent passive read found the PID unqueryable and no owned windows. No force termination or second close was issued. The WM_CLOSE API return boolean was not retained, so claim only that one close request was made and the target was absent at readback.

## Raw custody and next work

Raw conditions and trial files remain local-only in `private-packets/map01_native_windows_current_main_r179_abnormal_exit_20261114/`. The 171-entry post-stop manifest (including the frozen conditions) is `manifest-r179-r02-poststop.json`; SHA-256 `849f6eeea76e66626772aa11130a85f9f77501a603d33ab9f51a0ddf12e6841d`. All entries were re-read and matched size and SHA-256.

Next: correct the public result-query caller to assert fields at their actual envelope/action/cancellation scopes, and capture a fresh unoccluded same-frame ammo image before claiming the exact task effect. R179-R02 is not replayable and is not an abnormal-exit effect pass. Current-main native replication and the matched #57 all-trial efficiency comparison remain open.
