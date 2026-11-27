# Post-merge standard-caller Xvfb recheck

Source: exact main `96c3476e9c665d801d6f57814ff7241b868d5636`, following PR #10388.

The frozen public-caller blocked-release test ran once in normal mode and once under `-O`; both unittest runs exited 0 with captured private-Xvfb provenance. Both observed XRes disconnect and verified independent release readback. The public cancellation response remained `pending` while the finite recovery continued. At the 8.5 s horizon, the original task oracle failed because its effect count rose from 1 to 4 (normal) and 1 to 19 (`-O`). Event traces show repeated A KeyPress/KeyRelease while the original A obligation stayed held through the intentionally withheld cancel acknowledgement; the scheduled delayed B KeyPress was not observed. The separate fresh-generation task oracle passed once in both modes, with no old-input contamination. The original operation remained `cleanup_status=UNKNOWN`, `release_confirmed=false`, and `replay_allowed=false`; final A/B/C keymaps were all up.

This confirms the merged XRes timeout candidate on exact main. It does not close the original task-success or delayed-effect gate. Preserve the old failure and new-generation success as separate outcomes. No MAP01, real provider, matched efficiency, reliability rate, or Research Preview acceptance is established.
