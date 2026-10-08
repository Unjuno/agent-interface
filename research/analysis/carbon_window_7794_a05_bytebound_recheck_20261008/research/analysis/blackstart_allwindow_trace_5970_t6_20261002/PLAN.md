# Issue #5970 T6 — all-window observer vs server RECORD

## H / T / D / C / U

- **H:** Selecting KeyPress/KeyRelease on every currently mapped Tk X window from an independent X client will capture the exact recipient events identified by X RECORD, resolving whether T3/T4's Entry-only observer missed because it selected the wrong window.
- **T:** Reuse the hash-pinned T3-derived app in a fresh private Xvfb. A separate purpose-built observer recursively inventories the mapped window tree, selects both key masks on each window, then records delivered events. X RECORD concurrently retains server `FromServer` raw payloads. Send exactly one Shift press/release pair; unconditionally attempt release and verify terminal neutrality. Independently decode both raw streams and compare event recipient XIDs with the pre-dispatch tree/selection acknowledgments.
- **D:** `PASS_ALLWINDOW_CAPTURE` if RECORD sees exactly one press/release, the observer sees the same two event types/keycodes/times, the recipient XID was in its selected window set, cleanup release was attempted, and the keymap is neutral. `HOLD_TARGET_OUTSIDE_SELECTED_TREE` if RECORD sees the pair but its recipient was not among the successfully selected windows; `HOLD_OBSERVER_STILL_EMPTY` if in-tree recipient is selected but no events arrive. Any missing/malformed stream or non-neutral state is HOLD. No causal order from timestamps alone.
- **C:** One Tk app, one isolated Xvfb, one synthetic Shift pair, one X RECORD context, all-window observer. Docker Desktop engine remains unavailable at T5; use private WSL2 Xvfb and record the deviation. No user desktop or physical HID.
- **U:** Why target windows differ across runs; whether this event path transfers to deployed #4135; whether an observer can provide nonperturbing, trustworthy provenance; recovery reachability, task effect, and product benefit.

## One-shot

Candidate and independent raw audit each run once. No rerun of T3/T4 allocations or #4135 formal allocation. Always attempt release in finally; capture terminal keymap even after observer/RECORD errors.
