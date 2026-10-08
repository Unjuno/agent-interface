# Issue #5970 T8 — observe Tk window ancestors

## H / T / D / C / U

- **H:** The X RECORD recipient was the mapped parent/ancestor of Tk's `winfo_id()` root, not a descendant; selecting KeyPress/KeyRelease on that ancestor chain will let an independent observer capture the same events as X RECORD.
- **T:** Use the exact T3-derived app in a fresh private Xvfb. Before input, a separate observer selects both core key masks on the recursive Tk subtree and every parent through the X server root. X RECORD captures server-delivered events concurrently. Send exactly one Shift_L press/release pair, always release in finally, and query terminal keymap. Independent audit compares event types, keycodes, server times, recipient XIDs, and successful observer selections.
- **D:** `PASS_ANCESTOR_OBSERVER_CAPTURE` if RECORD/app/observer each contain exactly one press and release with matching keycode and server times, every RECORD recipient was successfully selected, and release/neutrality gates pass. `HOLD_ANCESTOR_NOT_SELECTED` if target selection failed; `HOLD_OBSERVER_EMPTY_OR_DIVERGENT` if the target was selected but streams do not match; safety or raw errors HOLD.
- **C:** One app, one private Xvfb, one synthetic key pair, no user desktop or physical HID. Docker Desktop engine unavailable at T7; use isolated WSL2 Xvfb and disclose fallback.
- **U:** Whether hierarchy/recipient behavior is stable across Tk/X server/WM versions; whether the observer's reception creates useful causal provenance; deployed #4135 behavior, recovery success, and task benefit.

Candidate and independent auditor each run once; no retries or formal #4135 allocation rerun.
