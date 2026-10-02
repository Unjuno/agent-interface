# Issue #5970 T6 — all-window observer trace

## Disposition

`HOLD_STREAMS_DIVERGE_OR_INCOMPLETE` (independent raw audit). In one bounded Shift pair, the exact T3-derived app logged KeyPress/KeyRelease, and server-side X RECORD retained both events with keycode 50 and times matching the app. The all-window observer logged zero. The RECORD recipient XID was `2097170`, while the observer successfully selected the enumerated set `{2097169, 2097171}`; the recipient was not in that set. Cleanup release was attempted and final keymap was neutral. The narrow hypothesis that recursively selecting the currently enumerated Tk window tree suffices was not supported.

Candidate/auditor ran once. Raw callback bytes, event rows, window inventory, and the selection acknowledgments are retained. No #4135 allocation was rerun. Docker Desktop remained unavailable; only private WSL2 Xvfb was used.

This outcome does not establish why X RECORD names a recipient absent from the recursively queried tree, whether that target was transient or represents a Tk/Xlib/X RECORD semantic boundary, or what observer architecture would recover provenance. No timestamps are used as causal edges. No physical input, deployed #4135 behavior, recovery benefit, task effect, or product claim follows.
