# TTC consecutive-confirm first outcome

Decision: **HOLD_CONFIRMATION_COST**.

The one changed mechanism was pre-final external executable admission: `CONSECUTIVE_CONFIRM` requires the same executable prediction at confidence >=0.90 on two consecutive stages. Training, data distributions, confidence threshold, model width/depth, epochs and external vocabulary remain the retained DIRECT_TTC configuration.

Across four fresh seeds, DIRECT_TTC shifted-stress premature executable counts were `[7,5,5,5]` (22 total); CONSECUTIVE_CONFIRM produced `[3,1,1,3]` (8 total), a 63.6% reduction. Candidate correctness gates had no violations and every seed stayed <=0.10% stress premature-exec.

The candidate is not retained for promotion because the frozen cost boundary failed: ordinary normalized compute was above 0.75 and stress compute above 0.85 in all four seeds. It remained mean-latency faster than FULL_DEPTH 4/4; median mean-latency reduction was 18.11%, but median p50 reduction was 14.04%, below the frozen 15% gate. Candidate p95 did not regress versus FULL_DEPTH in any seed.

Interpretation: two-stage confirmation is a real safety/latency tradeoff, not a free fix. Do not relax compute or p50 gates post hoc. A later successor should change the safety/readiness representation so confirmation can be selective, rather than sweeping confidence thresholds.
