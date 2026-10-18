# A14 run log

The frozen preflight passed for task rows 2–6, screenshot hashes/dimensions, per-task prompt/schema hashes, and the A12 candidate source before the first provider call. Each task was invoked once, sequentially, with a 90-second timeout and no retries. All five calls exited 0, did not time out, and returned schema-constrained output. Total elapsed provider-call wall time was 92.46 seconds. Captured usage totals: 68,930 input tokens (22,016 cached), 2,688 output tokens, including 1,121 reasoning-output tokens. These are provider counters, not money or end-to-end study cost.

The independent lifecycle audit passes under normal Python and `python -O`; each row's negative mutation adding `target_valid=true` to the entry action postcondition is rejected by the A12 candidate wrapper. Post-run qualitative image inspection found task 3's screen blank while its returned output gives a contract and task-2-like coordinates; see `VISUAL_REVIEW.md`. This does not change the frozen schema/lifecycle gate, but it rules out interpreting 5/5 candidate acceptance as 5/5 grounded outputs.

No GUI, application input, formal/live allocation, or effect scoring occurred. The original R02 outputs/scores are untouched.
