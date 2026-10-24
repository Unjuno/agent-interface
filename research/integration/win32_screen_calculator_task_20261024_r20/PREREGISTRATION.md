# R20 — paired UIA onset timing with standard Win32 caller

## Question
Can a continuously sampling independent UIA observer bound the exact Calculator display transition during one public supervised-Win32 task while the caller also records generation binding, input release, neutral readback, and an exact-schema task-success receipt?

## Frozen task
One +1= operation on the observed Calculator target HWND 55117672 / PID 35132. Pre-input display 1,045; expected display 1,046. Observe with screen_physical_px in [48,32,320,533], verify a nonblank image and unchanged target, then visually inspect before dispatch. A background UIA process brackets each CalculatorResults read with Stopwatch.GetTimestamp() QPC values at requested 10 ms cadence. Three consecutive pre-dispatch samples must show 1,045.

## Procedure and stop rules
1. Pin current main 212c5f1494d0c84f48c6b6ebbe64fb4c77c2bed7 (tree f9b12ec434ce48c0d084b884bb3bfcc136d035b6) and hash caller, scorer, monitor, conditions, and preregistration.
2. Confirm target identity, foreground root, visibility, region, and UIA baseline. Any mismatch is pre-input STOP.
3. Obtain one same-session public observation. Require a unique target generation, nonblank 320x533 image, and unchanged UIA/focus/geometry. Pause for visual review; dispatch only after PROCEED_R20.
4. Start independent UIA monitor; require three baseline samples before exactly one dispatch of +1= plus release. Stop if any pre-dispatch sample differs.
5. Invoke task verifier once, read retained results once, stop observer, and perform one separate UIA post-read. If pending, cancel that exact call once and poll its read-only result for at most 4 seconds; never replay. Never replay.
6. Preserve raw output. Audit call/operation/generation binding, verifier, release/custody, same-generation UIA transition, monitor exit, and hashes.

## Timing gate
Report the transition as an interval from the start timestamp of the last 1,045 read to the end timestamp of the first 1,046 read. This conservatively contains the state transition between negative and positive reads. Also report dispatch-start to first positive read-end. Neither interval is physical-key-to-effect latency. Report actual sample cadence and read errors.

## PASS scope
PASS_SCOPED only if the same generation is visually grounded, dispatch completes once, task verifier returns verified/task_success=true for the same call/operation/generation, release and neutral completion readback verify, the independent UIA monitor brackets 1,045->1,046 with no intervening value, and close leaves no unresolved call. Missing evidence is HOLD/UNKNOWN.

## Limits
One native Calculator sample. No MAP01, WSLc, blocked-I/O recovery, matched efficiency, or broad reliability claim. This fresh attempt is not a replay of R13-R19.
