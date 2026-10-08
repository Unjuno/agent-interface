# Recovery status — Issue #4799 pre-formal STOP

This archive preserves the four original source/pre-formal files from remote
branch `research/local-relevance-x11-gate-4799-20260927`, tip
`95620fefe1e9eb7b466f2b81c93689bf260520b8`. The historical Issue record says
the allocation stopped before `XGetImage`: the first launch found an already
existing output directory; the second reached Tk/Xvfb and stopped because
`Display.allowed_depths` was unavailable in the pinned Python-Xlib API.
No frame/pair, model fit/evaluation, or audit result was produced. This is an
environment/API STOP, not an ML outcome.

The remote branch does not contain a freeze file, formal output, or raw capture
bundle. The referenced failure outputs were described as local-only and were
not found in the current recovery workspace; nothing was reconstructed or
rerun. The original README, capture, training, and auditor source files remain
byte-preserved, but this archive must not be treated as a complete formal
evidence bundle.

Successors #4802 and #4807 are separate allocations, already retained on main
through PRs #4805 and #4811. Their outcomes do not revise or pool with #4799.
No source was edited after the historical allocation, and no X11 capture,
training, or audit was executed during this recovery.
