# R15 — corrected public standard-caller Calculator task

## Frozen question

Does one public `supervised-win32` caller attempt compose a client-bounds-valid observation, one fresh target generation, one exact-generation Calculator action, an independent UIA effect oracle, verified release, and neutral completion readback?

## Hypothesis

Given the same live Calculator target and a pre-action UIA display of 1,042, `interface_observe` over the exact measured 320×533 client region will return exactly one 64-hex target generation. One public `interface_dispatch` (`focus calculator`, `text +1=`, `release_all`) will then produce UIA display 1,043, with a terminal release receipt and `interface_verify_task` returning `task_success=true`.

## Procedure and stopping rules

1. Read-only UIA and Win32 preflight must confirm display 1,042, HWND 55117672, owner PID 35132, visible target, and target as foreground root.
2. Re-measure the target client rectangle in the runner. Stop before observation if it differs from `[0,0,320,533]`.
3. Send exactly one public `interface_observe` using `window_client` region `[0,0,320,533]`.
4. Stop before input if observation fails, no unique target generation is returned, the UIA baseline changes, or the target identity/foreground root changes.
5. Freeze the returned generation and source evidence into `run/FROZEN_TARGET.json` before dispatch. Then send exactly one public dispatch, with a 10-second authority lease and 10-second caller wait.
6. The independent UIA oracle polls exact result digits 1043 for at most 1,500 ms at 25 ms intervals. Invoke `interface_verify_task` once only if dispatch returned. Perform a separate post-verification UIA read and one neutral `interface_results` readback.
7. If dispatch is pending, cancel only its exact call once and poll only its retained result for at most 4 seconds. Never replay input. Close the MCP session and retain every raw response, error, image and receipt.

## Decision

PASS requires all of: exact call/operation/target-generation binding; completed action; `task_success=true` from the configured independent UIA oracle; separate post-check display 1,043; verified terminal release; neutral completion readback; zero unresolved calls; closed session. Missing or unbound evidence is UNKNOWN; contradicted evidence is FAIL. No outcome authorizes replay.

## Limits

Native Windows Calculator only; one attempt; no model call. The effect interval begins at the post-dispatch UIA oracle read, not the physical key event. This does not test WSLc, MAP01, blocked-I/O release, bounded recovery efficacy, matched efficiency or reliability. The existing Calculator remains at its resulting UI state; no restoration input is included.

R13 is retained as an observation setup stop caused by an oversized client rectangle. R14 is retained as a prelaunch runner/condition ID mismatch; neither attempt dispatched input.
