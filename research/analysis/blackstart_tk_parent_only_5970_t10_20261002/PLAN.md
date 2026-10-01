# Issue #5970 T10 — immediate-parent-only event selection

## H / T / D / C / U

- **H:** T9's extra observer Release / excess RECORD multiplicity arose from selecting both the immediate parent and its descendants; selecting only the immediate parent will capture exactly the intended Shift pair without the extra row.
- **T:** Fresh private Xvfb; exact T3-derived app; independent X observer selects KeyPress/KeyRelease only on the dynamically discovered immediate parent of Tk root. X RECORD runs concurrently. One Shift_L press/release, unconditional cleanup and terminal keymap query. Independent audit compares raw server events and app/observer streams.
- **D:** `PASS_PARENT_ONLY_EXACT` if app, observer, and X RECORD each reduce to exactly one press/release at keycode 50 and matching server times, recipient is the successfully selected parent, release attempted, neutral keymap. Any extra/missing/different event or safety issue remains HOLD with raw details.
- **C:** One input pair in a private Xvfb; no user desktop or physical HID. Docker Desktop unavailable at T9; WSL2/Xvfb fallback.
- **U:** Whether extra delivery was due overlapping selection or something else; stability across server/Tk/WM; provenance transfer to #4135 and any recovery/task benefit.

T10 is a distinct one-shot successor to T9's stream-cardinality HOLD. No candidate/auditor retries and no formal #4135 allocation rerun.
