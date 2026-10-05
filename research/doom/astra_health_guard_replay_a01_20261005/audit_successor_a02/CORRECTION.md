# A02 correction to the A01 threshold replay audit

The reviewer of PR #7913 correctly noted that A01's first audit checked the
five expected hard floors and first-crossing timestamps, but did not
independently reconstruct every row in `raw.json`. The A01 disposition and raw
are unchanged; its audit is therefore a summary-level cross-check, not a full
independent replay audit.

A02 adds a separate read-only auditor. It rebuilds all five threshold tables
from the exact 10-row manual `VISUAL_READOUT.json`, including every evaluated
sample, health, phase, status, reason, hard floor, stop row, and first
invalidation. It compares the complete reconstructed structure with the
one-shot A01 raw. The candidate and production guard were not rerun. The
first two A02 auditor construction failures are retained in `AUDIT.json` and
`recheck-01/AUDIT.json`; the corrected full reconstruction passes in
`recheck-04/AUDIT.json` on the branch merged with current main (5 threshold
rows, 30 evaluated rows). `recheck-03/AUDIT.json` preserves the preceding pass.
Three focused
mutation tests reject changed fields and missing, reordered, or extra rows.

This corrects only the evidence-integrity limitation raised for the threshold
table. A02 independently reconstructs the arithmetic implied by the frozen
guard contract; it does not independently establish the correctness of the
production guard implementation, the manual video transcription, live sensor
cadence, planner scheduling, cancellation latency, release, recovery, or game
effect. The original live threat-exposure gate remains open.
