# Issue #5970 T11 — non-modifier control for parent-only event trace

## H / T / D / C / U

- **H:** The extra KeyRelease observed before/at the Shift press in T9/T10 is specific to modifier-key handling; a normal `a` press/release observed on the same Tk immediate-parent window will yield an exact two-event app/observer/X RECORD trace.
- **T:** In a fresh private Xvfb, use the exact T3-derived app and the already hash-pinned T10 parent-only observer. Query initial A keymap neutrality, arm server-side X RECORD, send one `a` press/release pair, attempt cleanup release in finally, then verify terminal A neutrality. Independently parse and compare event types, keycodes, times, recipient IDs and selected parent.
- **D:** `PASS_NONMODIFIER_EXACT` if all three streams contain exactly one KeyPress/KeyRelease for the dynamic `a` keycode with matching server times and selected target, and release/neutrality pass. Extra/missing records or nonneutrality HOLD with raw evidence.
- **C:** One key pair in private Xvfb; app Entry receives the character only. No user desktop or physical HID. Docker Desktop engine unavailable; WSL2 Xvfb fallback.
- **U:** Whether any extra Shift record is modifier-specific, whether RECORD multiplicity reflects per-client delivery, runtime/Tk/X server stability, and any #4135 recovery/product relevance.

One candidate and one independent audit; no T9/T10 retry or #4135 formal allocation rerun.
