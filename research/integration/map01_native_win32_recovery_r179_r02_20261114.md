# MAP01 native Win32 recovery R179-R02 (2026-11-14)

## Classification

`PARTIAL_EVIDENCE_STRICT_PREREGISTRATION_FAIL`. The trial performed one native LEFTDOWN and did not replay it. Its public terminal record preserves the source action as `unknown`, `release_confirmed=false`, `task_success=null`, and `replay_allowed=false`; a separate cancellation result says `recovered` and `release_confirmed=true`. The runner stopped at its conservative top-level projection assertion before its own post-stop checks completed.

The retained terminal shape explains the assertion: the query envelope has `input_dispatched=false` and no `release_confirmed` value; the nested source action has `input_dispatched=true` and `release_confirmed=false`; the cancellation is a separate recovered result. Do not promote cancellation release evidence to the source action or treat the harness assertion as a passing attempt.

## Current-main caller cross-check

The runtime query shape is already covered by `SupervisedWin32MCPTests.test_compiled_graph_routes_each_action_through_supervised_dispatch` on current main. It asserts that `interface_results` returns `input_dispatched=false` at the query envelope while retaining `input_dispatched=true` under the original action. The focused test passed 1/1 under CPython 3.11.9 normally and 1/1 under `-O`. This is local fake-backed integration coverage, not native GUI evidence. The R179-R02 failure was its private runner incorrectly requiring top-level `release_confirmed=true`; the next runner candidate must assert action and cancellation scopes separately. That runner mismatch does not require a runtime query rewrite.

## Recovery release attempt receipt retention

A separate local code-path audit found that `win32_supervisor_helpers._recover` returns native release attempts, including `button_up` `SendInput` call-started and return-count fields, but `OperationCancellationSupervisor._run_recovery` previously forwarded only key-up attempts to `OperationOwner`. Consequently a public cancellation record could report release confirmation while omitting the native button-up attempt ledger. The candidate fix forwards the bounded receipt and stores validated copies as `recovery_release_attempts`; it does not promote an attempt receipt into release confirmation. Regression coverage checks helper-to-owner forwarding, retained public owner result, and rejects a boolean ordinal. This code fix is separate from the R179 runner assertion and does not change or upgrade R179-R02's UNKNOWN effect classification.

Local verification on CPython 3.11.9: 145 tests passed normally and 145 passed under `-O` across process cancellation, operation owner, supervisor helpers, public supervised Win32 MCP, and backend release ledger. No native GUI trial was run for this code change.

## Evidence

- Frozen source: `06450f80e4e9b36ac1bbe604550e99380cbc98aa` (tree `1382c11ef45a23fb5d7d235bfbe3f3f946b0a9c8`).
- Attempt: `map01-native-auto-completion-recovery-r179-r02-20261114`; one accepted Win32 LEFTDOWN, producer exited 86, cancellation reported automatic recovery, replay denied.
- Cancellation record: 2,000,000,000 ns late-input interval, 78 observations, maximum observed gap 32 ms, and same-generation neutral readback. Its strict `late_input_horizon_verified` field is absent and `recovery_release_key_up_attempts` is empty.
- After the runner stopped, an independent read-only horizon verified 2 seconds of LEFT/W-up with the same process identity and target generation (176 samples, maximum sample gap 13.3955 ms). This is post-stop evidence and does not repair the strict runner failure.
- A public `interface_observe` call returned with matched generation. Its screen capture was occluded by another window in the registered ammo ROI; the preregistered classifier returned UNKNOWN (all four template distances 1.0). A second `window_client`/PrintWindow capture was black and also UNKNOWN. A partial visible HUD strip showed 49, but neither capture qualifies the preregistered effect oracle. The exact 50→49 effect therefore remains unverified; `task_success` remains null.
- One bounded exact-owned WM_CLOSE request was attempted after verifying the neutral horizon and process/HWND/generation binding. The wait reached a signaled process handle, then the helper failed while retrieving the exit code because the auxiliary ctypes prototype was not configured. A subsequent passive read found the PID unqueryable and no owned windows. No force termination or second close was issued. The WM_CLOSE API return boolean was not retained, so claim only that one close request was made and the target was absent at readback.

## Raw custody and next work

Raw conditions and trial files remain local-only in `private-packets/map01_native_windows_current_main_r179_abnormal_exit_20261114/`. The 171-entry post-stop manifest (including the frozen conditions) is `manifest-r179-r02-poststop.json`; SHA-256 `849f6eeea76e66626772aa11130a85f9f77501a603d33ab9f51a0ddf12e6841d`. All entries were re-read and matched size and SHA-256.

Next: update the private native runner gate to match the already-tested envelope/action/cancellation scopes, then freeze a new attempt with an explicit foreground/capture check before effect adjudication. Capture a fresh unoccluded same-frame ammo image before claiming the exact task effect. R179-R02 is not replayable and is not an abnormal-exit effect pass. Current-main native replication and the matched #57 all-trial efficiency comparison remain open.
