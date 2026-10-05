# Pre-registration: V39 release projector attempt ordinal type boundary

Date: 2026-10-05 (Asia/Tokyo)
Question: Does current main `19a6b723e58ccfd2b8265e88659589ef9223fcc9` accept JSON boolean `true` as retry ordinal 1, incorrectly making release measurement ready?

H: `_valid_pair` compares `attempt.get("attempt") != index`; Python equality treats `True == 1`, so a structurally malformed receipt is accepted.

T: Add one focused regression that first checks the untouched valid singleton fixture is ready, then changes only the first attempt ordinal from integer 1 to boolean `true`. Run that test once against the frozen production source before repairing it. A failure of the regression means the malformed receipt was accepted. Do not repeat the baseline probe.

D: Reproduce: positive control ready and mutated receipt still ready (expected regression failure). Repair: require an exact integer ordinal and equality to its one-based position. Then run the focused regression and complete projector unit suite.

C: Synthetic receipt/schema boundary only. No key event, GUI, native input owner, application consumption, game behavior, or live MAP01 outcome is measured. No container allocation is needed for this pure standard-library predicate test.

U: This result applies only to the frozen projector on the stated main SHA and the specified one-field mutation. It does not establish overall release-projector correctness or authorize #59's live lane.
