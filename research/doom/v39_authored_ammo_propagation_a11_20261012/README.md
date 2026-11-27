# A11 — authored ammunition validity versus pending fire cover

This experiment compares two actual current-main source boundaries at a positive ammo count. The planner action contract is authored with `minimum_ammo=5`; its current-action admission is checked against ammo 4 while the exact `build_cover_monitor` is observing the same source/current epochs as a fire cover.

## Result

The action admission rejected ammo 4 with `ammo_minimum_failed`. The paired cover monitor did not invalidate at ammo 4: it recorded one soft event, and its ammo hard floor was 1. At ammo 0, that same monitor invalidated with `ammo:below_hard_minimum`. Both tests passed in WSLc. Source blob IDs, byte counts, SHA-256 values, raw transcript, structured receipts, and the corrected independent audit are retained in this package.

This demonstrates a difference between the planner's immediate action predicate and the cover monitor's positive-ammo floor. It does **not** by itself prove a bug: these may be intentionally separate policy contracts, and this fixture does not establish that an active cover is required to honor a next-action minimum. The result identifies a decision the live allocation must make explicit.

No Doom/model/GUI/OCR, pending-model cancellation, actual ammo consumption, input, physical release, useful feedback, recovery, progress, task effect, or terminal result was tested. This is source-boundary construction evidence only.

See `HYPOTHESIS.md`, `RUNS.md`, and `DEVIATION.md`. The first independent auditor attempt is preserved in `results/audit_attempt1.json`; its classifier defect was corrected without rerunning tests.
