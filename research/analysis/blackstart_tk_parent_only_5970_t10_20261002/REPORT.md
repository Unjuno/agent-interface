# Issue #5970 T10 — parent-only observer

## Disposition

`HOLD_PARENT_ONLY_STREAM_DIVERGENCE` (independent raw audit). Selecting only immediate-parent XID 2097170 still yielded three observer events: a KeyRelease at the press timestamp, then KeyPress at that same timestamp, then the cleanup KeyRelease. The source-derived app logged the expected two rows. X RECORD retained five delivered-event records (two press records and three release records), all on keycode 50 and target XID 2097170. Release was attempted and terminal keymap was neutral. Exact two-row equality failed; the extra event was not discarded or normalized away.

The extra Release persisted with only the parent selected, so overlapping descendant selection does not explain it. This single-run result does not establish why it occurs or justify a product/recovery claim. Docker Desktop unavailable; private WSL2 Xvfb fallback; no #4135 formal allocation rerun.
