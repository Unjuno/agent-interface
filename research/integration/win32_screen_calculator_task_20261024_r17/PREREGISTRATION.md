# R17 — visually gated screen-observation Calculator task

## Question and hypothesis

Using the same live Calculator target, can a public supervised-Win32 caller use the visually useful `screen_physical_px` observation, bind one `+1=` dispatch to its exact target generation, obtain independent server-side UIA `task_success=true`, and verify release plus neutral completion readback? Baseline is UIA-verified 1,043; expected result is 1,044.

## Frozen conditions

Target HWND 55117672 / PID 35132; screen region `[48,32,320,533]`; baseline 1,043; same current-main source and Win32 backend as merged `21f53e7ed7ce200fe4959a858b59160f81569e21`. The R16 read-only capture at this region visibly showed 1,043; R15’s client capture at equivalent dimensions was uniformly black.

## Procedure and stop rules

1. Verify UIA display 1,043, exact HWND/PID, visibility, foreground root and unchanged physical region.
2. Make one public `interface_observe(screen_physical_px)` call in the same server session. Require a returned receipt with one 64-hex generation and nonblank 320×533 image; repeat UIA/focus/geometry checks.
3. Pause before dispatch. The operator visually inspects the saved screenshot and proceeds only if it visibly shows Calculator at 1,043. Otherwise abort and close without input.
4. If approved, dispatch once: focus Calculator, type `+1=`, release all. Use the exact frozen observation sequence, binding revision and target generation; 10-second authority and wait bounds.
5. If dispatch returns, invoke `interface_verify_task` exactly once for that call. The configured UIA oracle polls 1,500 ms at 25 ms intervals for exact 1,044, binding call, operation and target generation. Then read retained results and UIA once. If pending, cancel only that exact call once and poll its retained result for at most 4 seconds. Never replay.
6. Close and retain every receipt, raw response, screenshot and error.

## Decision

PASS requires same call/operation/generation throughout, one dispatched action, UIA oracle `task_success=true`, separate post-check 1,044, verified terminal release, neutral completion readback, closed session and no unresolved calls. Missing or unbound evidence is UNKNOWN; contradiction is FAIL. No result authorizes replay.

## Limits

One Calculator transition on native Windows. No WSLc, MAP01, blocked-I/O recovery, matched efficiency or reliability claim.
