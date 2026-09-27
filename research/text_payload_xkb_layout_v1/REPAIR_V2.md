# V2 repair rationale

Formal v1 consumed result `text-payload-xkb-layout-v1-20260916-01` and failed only the frozen in-server map-restoration gate. It is retained unchanged.

A separate diagnostic showed: baseline mapping width 7; after projection the server still reported width 7; attempting to restore the saved baseline caused XKB/core normalization to width 15, changing all 248 rows. Therefore byte-exact in-server restoration is not available through this fixture mechanism.

V2 does not reinterpret that failure. It allocates a new question with process-level isolation: fixture mutation occurs before candidate execution inside a fresh private Xvfb, candidate invariance is measured, and the server is discarded at arm end. This prevents fixture state from crossing arms while keeping the non-transparent setup explicit.
