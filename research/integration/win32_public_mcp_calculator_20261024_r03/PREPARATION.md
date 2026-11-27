# R03 — tracked runner session for the public MCP Calculator task

R01 and R02 are preserved unchanged. R02 obtained a valid `screen_physical_px` observation but the interactive process session was not retained by the orchestration wrapper, so it stopped before validation and input. R03 changes only the harness custody: retain the returned process session ID, review the new screenshot, and send the frozen `DISPATCH` token only if the screen still matches the frozen Calculator Standard-mode/0 precondition.

The attempt uses current main, the public `supervised-win32` stdio MCP route, and the same single task `314 + 728 = 1042`. Limits remain one observation, one validation, one dispatch, up to five exact result polls, no recovery, no replay, and a 90-second wall-clock bound. All uncertain outcomes stop as UNKNOWN. A fresh post-action observation is permitted only after terminal completion and release receipts. Task success stays null; visual evidence is scored separately.

This is on the user-authorized local Windows PC. WSLc and Docker are not used. No user files are in scope.
