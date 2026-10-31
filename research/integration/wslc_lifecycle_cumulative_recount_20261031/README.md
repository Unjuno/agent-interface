# Cumulative recount of WSLc lifecycle comparisons

This is an offline recount of four previously published experimental packets, not a new live run. `audit.py` verifies each packet's SHA-256, runs its original audit, and recomputes cumulative preflight and per-task usage from its raw records. Run `python audit.py` from any directory. `audit-result.json` is the resulting machine-readable record.

| Block (seed) | First task where persistent input is lower | First task where persistent partial time is lower | First task after which persistent partial time stays lower through task 6 | Ephemeral status |
|---|---:|---:|---:|---|
| forward (991028) | 2 | 2 | 2 | 6 completed |
| reverse (991028) | 2 | 2 | 2 | 6 completed |
| first-newseed (991029) | 2 | 1 | 1 | task 6 failed; usage unknown |
| resilient (991032) | 2 | 3 | 5 | 6 completed |

Input includes the preflight model call and all recorded task model calls. Persistent input starts 186 tokens higher after task 1 in each block, but is lower from task 2 through task 6 in these four fixtures. The first two blocks use the same seed and are not independent benchmark tasks. In the resilient block, persistent's partial time is lower at task 3 (20.29 s versus 20.96 s), higher again at task 4 (25.95 s versus 25.08 s), then lower from task 5 through task 6. A first crossover therefore does not establish a stable break-even point.

Partial time is the sum of the measured preflight duration and each measured task interval. It excludes process startup, gaps, independent scoring, and cleanup; it is not end-to-end latency. Each arm's separately recorded lifecycle time is included in the JSON, with its original limitations. Token counts are not monetary costs, and cached input is not added again. Conditions, toolsets, seed, arm order and host error handling vary among blocks. One run per condition on a small fixed fixture does not establish general speed, reliability, statistical significance, or a frontier claim.

For first-newseed ephemeral task 6, a host permission error led to a timeout and its model usage is unavailable. Its cumulative input is `null`, not zero or an exact total. The recorded 86,342 tokens are a lower bound based on the preflight and recorded calls through the first five tasks. The report preserves the failed task and its observed elapsed interval; it does not impute usage or count that task as a success.

Source packets and audits are in sibling directories: `wslc_three_arm_lifecycle_20261031`, `wslc_three_arm_lifecycle_reverse_20261031`, `wslc_three_arm_lifecycle_first_newseed_20261031`, and `wslc_three_arm_lifecycle_resilient_20261031`. The original packets remain the authority for task outcomes, input-release events and full conditions. This recount does not close issue #57 or establish MAP01/live control completion.
