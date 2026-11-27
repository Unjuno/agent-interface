# R13 — one public standard-caller Calculator task

## H/T/D/C/U

**H.** On this attached Windows PC, when the live Calculator target generation is obtained through interface_observe and its UIA display is exactly 1,042, one standard supervised-win32 interface_dispatch containing the literal text +1= should produce the independently observed display 1,043 and verified neutral input release.

**T.** One public observation, one exact-generation standard dispatch, one server-configured independent interface_verify_task invocation, and one additional read-only UIA read. The task is not replayed. The UIA oracle may poll for at most 1,500 ms after the terminal action, every 25 ms. If the dispatch remains pending after its caller wait, issue one exact-call cancellation and poll only that call's retained result for up to 4 seconds.

**D.** PASS requires exact call/operation/target-generation binding, task_success=true from the configured independent UIA oracle, exact display 1,043 in a separate post-verification UIA read, verified terminal release and neutral completion readback, and no unresolved process/call. A mismatch is FAIL; missing, timed-out, or unbound evidence is UNKNOWN. No result authorizes replay.

**C.** Keyboard routing could be affected by the visible overlapping window; Calculator may not accept Unicode text input; the UIA read may lag the app; the target HWND could change. Fresh foreground-root, process, public observation and generation checks gate the single dispatch.

**U.** This is one native-Windows Calculator sample. The effect observation interval starts at a UIA polling read after dispatch completion, not at the physical key event. It does not estimate efficiency, reliability, WSLc behavior, or MAP01 transfer.

Task effect is display-only: continue the existing 314 + 728 calculation by one and read 1,043. No file is saved. The run must stop before input if the initial UIA value is not exactly 1,042, the target identity changes, the target is not the foreground root, or the public observation lacks one matched target generation.
