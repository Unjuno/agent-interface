# R03 result: disabled-auto-repeat mechanism control

The one-shot Docker/Xvfb calibration completed with exit code 0. Global auto-repeat was explicitly disabled through `ChangeKeyboardControl(auto_repeat_mode=Off)` and read back as 0 before keydown. The exact private Xvfb process was stopped/resumed via pidfd for 4,000.224 ms. The receiver recorded only the initial A KeyPress and the explicit A KeyRelease; there were zero post-resume repeated A KeyPress events. Independent keymap readback after release found A up.

Combined with the separate enabled-auto-repeat calibration (global mode 1, two post-resume A KeyPress events 39.879 ms apart), this strengthens the interpretation that the R02 pair of extra A effects at 39.872 ms spacing is compatible with X server auto-repeat. The disabled control does **not** establish the exact R02 cause: it was a separate synthetic XTEST sender/receiver, not the blocked MCP runtime path; queued or replayed transitions remain possible. R02 stays failed for old-task effect count, runtime release/cleanup UNKNOWN, replay denied.

r01 and r02 of this disabled-control setup stopped before any key event or pidfd pause because of setup mistakes; their logs/conditions are retained separately. r03 was preregistered as a distinct one-shot before execution. The raw result's internal schema string says `...r01` because the script was copied from the first calibration; packet identity is established by its conditions and invocation metadata. The raw is unchanged.

Limits: one synthetic Linux Xvfb calibration per enabled/disabled setting; not MCP cancellation or recovery, native Windows input, WSLc, MAP01, reliability, nor an efficiency score.
