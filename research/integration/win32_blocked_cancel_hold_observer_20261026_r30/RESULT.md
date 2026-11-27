# Win32 held-callback state discriminator R30

Date: 2026-10-26. Source main at execution: `575ce5665086f2cdfa108bace9ae9a82933aac25`; source tree: `a7a57f7c8793e102709eeaec57a249bd8c3c1947` (runtime tree unchanged on current main `991c94da860fcc57b0bc178ccdcd5e80ef712ddc`).

## Result

One fresh native Win32 synthetic-fixture trial passed its scoped audit (14/14). The visible exact fixture (PID 58760 / HWND 200216) passed CUA activation and both exact foreground checks. The standard public caller dispatched one call (`9e81c88ec6b3422e80cc60c0562718e2`) and operation (`e147ef0fb3e14bf3a73e1f6f12aa6bd4`) under generation `a85adfcbbe80176020d8fb33ef24789191611bf36db2fa92054800ae36821c87`. The independent fixture event log and task receipt verified exact token `R30T8K5H`, bound to that call, operation and generation.

An injected left-Ctrl down entered the low-level hook and remained blocked across public cancellation. Cancel returned `pending` in 1.888 ms. During the hold, an independent same-generation observer ran about 105.4 ms after cancel response and read Ctrl-up; the public same-call status poll still reported `action=running`, `cancellation=pending`. The manual gate opened 215.8 ms after cancel response, before the 500 ms failsafe; callback return followed 0.3185 ms later. Terminal recovery completed 19.2069 ms after callback return, then reported release confirmed and replay denied. Independent same-generation readbacks found Ctrl-up immediately after recovery and 1.828 s later. The terminal runtime task outcome stayed null; the separate task verifier returned success for the token effect that preceded Ctrl-down. Hook/server/fixture cleanup passed and the exact fixture exited 0.

## Interpretation limit

The `ctrl_down=false` held-state observation is not proof of release. Microsoft documents that `LowLevelKeyboardProc` runs before asynchronous key state is updated; while its callback has not returned, a concurrent read may still report the previous up state. The public call also remained `running/pending` at that sample. Thus R30 shows bounded cancel response and preserves UNKNOWN/pending while the callback is held; it does not establish a release completed during the blocked interval. Release confirmation and final neutral readbacks followed opening the callback gate. See [Microsoft's LowLevelKeyboardProc documentation](https://learn.microsoft.com/en-us/windows/win32/winmsg/lowlevelkeyboardproc).

This is one same-PC synthetic fixture sample, not an arbitrary OS/kernel-I/O guarantee, broad reliability estimate, MAP01 result or efficiency comparison. No WSLc, Docker, model or provider was used. R28 and R29 remain separate outcomes.

## Evidence custody

The 8-file frozen input manifest and post-trial 52-file manifest passed hash verification. Raw protocol receipts, event logs, held-state observer and status sample, post-recovery observers, images, exact conditions, and audit are retained locally at `C:\Users\user\Documents\Codex\2026-10-03\new-chat-2\private-packets\win32_blocked_cancel_hold_observer_20261026_r30`; the private packet is not part of this commit.
