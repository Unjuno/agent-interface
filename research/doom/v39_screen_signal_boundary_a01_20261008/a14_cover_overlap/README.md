# A14 posthoc overlap analysis

This is a posthoc descriptive analysis of A14, whose original freeze/run mismatch remains a protocol deviation. It is not a preregistered or valid efficacy result.

The analyzer intersects six planner-pending intervals with seven accepted-cover intervals using event timestamps, then counts adjacent typed observations only within each nonempty intersection. In the retained A14 trace, 146 observations formed 139 adjacent pairs. All 139 pairs had a changed whole-frame RGB hash; health and ammo were both unchanged in 128 pairs. The overlap spans ran from 1.208 to 9.973 seconds (varies by cover/turn pair).

These counts show that a naive full-frame-hash cancellation rule would fire repeatedly during the observed cover/wait overlaps, even when the two typed HUD values stayed constant. They do not say those frames carried meaningful threat information, that the cover was appropriate, or that any of those changes should have canceled it. The A14 run is exploratory and no causal, safety, recovery, or task-success conclusion follows.

`analyze_overlap.py` checks both source-file SHA-256 hashes and byte counts before producing `reduced_trace.json` and `RESULT.json`. `audit.py` independently recomputes all interval intersections and adjacent-pair counts. Its initial label-check implementation failure is preserved in `AUDIT_INITIAL_FAILURE.json`; it was corrected to recognize the canonical status label, without changing candidate inputs or counts.