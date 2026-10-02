# Issue #5970 T5 — X event target and mask ownership

## Result

`HOLD_T4_EVENT_WINDOW_NOT_IN_NO_INPUT_TREE`. The no-input candidate preserved a two-window tree (Tk root 2097169, Entry 2097171). `all_event_masks` had the KeyPress bit on both windows; a separate observer connection successfully selected KeyPress on Entry and on the root, with no BadAccess. Therefore this trial does not support an exclusive-mask-conflict explanation. T4's independently decoded event recipient 2097170 was absent from the T5 no-input tree, so this experiment cannot show whether selecting that exact transient/different recipient would capture events. Full raw candidate and independent audit are retained.

The frozen expectation that an app-selected target would reject a second client's selection was falsified for the tested root. Do not promote the untested target-mismatch explanation: its target did not appear in this no-input fixture. T6 will compare an all-window observer with X RECORD during one bounded press/release to identify the recipient against the live tree.

No input was dispatched in T5. This remains a source-derived private-Xvfb mechanism diagnostic, not a recovery or production claim.
