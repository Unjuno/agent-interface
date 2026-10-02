# Issue #5970 T9 — select Tk's immediate parent window

## H / T / D / C / U

- **H:** Selecting KeyPress/KeyRelease on the immediate X parent of Tk's `winfo_id()` root, plus its descendants, captures the events whose X RECORD `window` is that mapped parent (T7 found it present and selectable before input).
- **T:** In a fresh private Xvfb, use the exact T3-derived app. A separate observer discovers the immediate parent dynamically, recursively selects both core key masks on that parent and its descendants only (not the screen root), and records events. X RECORD runs concurrently. Dispatch exactly one Shift_L press/release pair; always attempt cleanup release and query terminal keymap. Independent audit compares event rows, times, recipient IDs, source hashes, selection receipts, release, and neutrality.
- **D:** `PASS_PARENT_WINDOW_CAPTURE` if app/RECORD/observer each contain exactly one press/release with matching keycode and server times, every RECORD recipient is selected, release was attempted, and keymap is neutral. If no matching observer event, `HOLD_PARENT_SELECTED_EVENT_MISSING`; target selection failure or malformed stream HOLD.
- **C:** One isolated Tk/Xvfb fixture, one synthetic Shift pair, no physical/user-desktop input. Docker Desktop remains unavailable; use private WSL2 Xvfb.
- **U:** Whether immediate-parent routing is stable across X server/Tk/window-manager versions, whether this yields trustworthy provenance for deployed #4135, and whether any recovery/task benefit follows.

T8's full-ancestor enumerator timed out before input; it is retained separately and will not be rerun. T9 candidate/auditor each run once; no #4135 formal allocation rerun.
