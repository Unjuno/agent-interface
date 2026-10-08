# Issue #5970 T7 — pre-input target XID liveness

## Disposition

`HOLD_TARGET_PRESENT_MAPPED`. Before any input, the exact T4/T6 X RECORD recipient XID 2097170 existed, was viewable (`map_state=2`), and accepted KeyPress/KeyRelease selection from the separate query client. It was not in the Tk `winfo_id()` subtree `{2097169, 2097171}`; its parent was X server root 543 and its child was Tk root 2097169. No XTest/input was dispatched. The independent raw auditor checked the saved candidate and T3 app identity.

This establishes pre-input liveness/selectability only in this private Xvfb construction. It suggests the missing target is the immediate parent of Tk's client window, but does not establish event-routing causality, deployed #4135 behavior, recovery, or task benefit.
