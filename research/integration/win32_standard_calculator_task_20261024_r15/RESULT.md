# R15 result — observation returned, but the image was black and task verification was skipped

## Disposition: HOLD_NOT_PASS

The corrected client rectangle let the standard public `interface_observe` return a 320×533 `window_client` frame and one target generation. The frame artifact is uniform RGB black (PNG SHA-256 `a0f2ac5ee8c6fda353c961511a02473b297fa5a16a50d5080df027eb830434d4`), so this is not usable visual evidence. The runner nevertheless dispatched its preregistered one-shot action using prior UIA-known state; treat the action as a bounded known-input test, not an observation-driven computer-control success.

The one dispatch completed on call `936af3dc904444918b7500470e9b9d61`, operation `14d5d99fd53b4a31960fe11814453264`, target generation `6c8471d23316dfac526a53a0249470c0289b6744ab2124b19b24df8d9f321c7c`. The action receipt reports `input_dispatched=true`, `release_confirmed=true`, an empty verified release state, and a neutral completion readback bound to the same operation and generation. Independent post-action UIA reads show 1,042 before and 1,043 after (`1042 + 1=`). Replay is denied and the session closed with no unresolved calls.

The strict task-effect gate did not pass. The runner inspected `dispatch_result.get("status")`, but the public wrapper places `status="returned"` under `dispatch_result["receipt"]["report"]`. It therefore skipped the preregistered `interface_verify_task` call; there is no `task-verification.json` or oracle receipt, and runtime `task_success` remains null. This verifier is process-local and no restart recovery is implied, so no post-close call was made and the action was not repeated. `interface_close.release_confirmed=false` refers only to release performed by close; the completed dispatch separately records release and neutral readback as verified.

## Reproducibility

`audit_r15.py` reads the immutable raw receipts, image, UIA records, frozen target and checksum manifest. Running it reproduces `run/audit.json`. The preregistered runner, conditions, UIA reader and preregistration hashes still match `FROZEN_SHA256SUMS`.

R13 remains the earlier bounds stop; R14 remains a prelaunch attempt-ID consistency stop. Neither dispatched input. R15 is the first corrected-bounds dispatch in this packet family, but it does not validate the visually observed control loop or runtime task-success integration.

## Next useful step

Fix the standard-caller response unwrapping and add a no-input regression that confirms returned dispatch receipts trigger the configured task verifier. Separately diagnose why `PrintWindow` yields an all-black Calculator client capture despite a foreground target. Do not replay this Calculator action; use a new, separately frozen task only after the observation route is usable.
