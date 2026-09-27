# LOCAL-SYSTEM1-TTC-CONSECUTIVE-CONFIRM-20260917-001

H: with exact DIRECT_TTC learning/data/confidence fixed, requiring the same >=0.90 executable prediction at two consecutive stages before early external admission will reduce premature shifted-stress executable decisions while retaining useful early-exit speed.
T: fresh seeds 9101701..9101704; same weights/rows compare FULL_DEPTH, DIRECT_TTC, CONSECUTIVE_CONFIRM. One case process/seed, no rerun.
D: exact gates are those recorded in Issue #913; HOLD_NO_SAFETY_DISCRIMINATOR if both early policies have zero stress premature executions on all fresh seeds; HOLD_CONFIRMATION_COST if safety improves but cost/tail gates fail.
C: confirmation may simply add one stage and worsen tail latency; two consecutive wrong predictions may persist.
U: synthetic structured-state TTC mechanism only; no action authority or real GUI/model claim.
