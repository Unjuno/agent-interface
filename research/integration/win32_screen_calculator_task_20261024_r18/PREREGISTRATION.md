# R18 — strict-schema screen-observation Calculator task

## Question and hypothesis

Can one public supervised-Win32 path compose a visually checked physical-screen observation, exact target-generation dispatch, exact-schema independent UIA task verification, and neutral release? Baseline is UIA-verified 1,044; one `+1=` should produce 1,045.

## Conditions

Use the same live Calculator HWND 55117672 / PID 35132, physical-screen region `[48,32,320,533]`, and current main `21f53e7ed7ce200fe4959a858b59160f81569e21`. R16 showed this capture mode displays the app. R17 separately proved the action/release path and UIA read, but its one-use verifier rejected an 11-key receipt where the contract requires exactly seven keys. R18 returns exactly `call_id`, `operation_id`, `target_generation`, `oracle_id`, `outcome`, `observed_monotonic_ns`, `evidence_ref`; timing and UIA detail remain in a separate local record and are never sent as receipt fields.

## Procedure and stop rules

1. Verify UIA display 1,044, target HWND/PID, foreground root and unchanged physical region.
2. Observe once through `screen_physical_px`; require one generation, nonblank expected-size image, and unchanged UIA/focus/geometry. Pause for visual inspection; dispatch only if the image visibly shows Calculator at 1,044.
3. Dispatch exactly once with `focus`, `text +1=`, `release_all`, bound to that observation’s sequence, binding revision and target generation.
4. If dispatch returns, invoke `interface_verify_task` exactly once for that call. The configured UIA oracle polls exact 1,045 for at most 1,500 ms at 25 ms. Then perform one retained-results read and one independent UIA post-read.
5. If dispatch is pending, cancel only that call once and read-only poll its result up to 4 seconds. Never replay. Close and retain raw results.

## PASS gate

The same call/operation/generation must bind dispatch, release and task certificate; task verification must say `verified` and `task_success=true`; separate UIA must show 1,045; terminal release and neutral completion readback must be verified; close must leave no unresolved calls. Any missing/invalid evidence is HOLD/UNKNOWN; no retry.

## Limits

One native Calculator transition only. No WSLc, MAP01, blocked-I/O recovery, matched efficiency or reliability claim.
