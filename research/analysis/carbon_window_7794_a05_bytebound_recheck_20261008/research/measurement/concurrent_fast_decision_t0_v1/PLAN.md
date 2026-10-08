# #1378 T0 concurrent fast-decision shadow

Parent: #1376.

H/T/D/C/U are frozen in Issue #1378. This is a no-task-input shadow discriminator. Frontier request/return stays 0/40 ms in every arm and every case. The deterministic lane samples at 5 ms cadence and can emit only ADVANCE/WATCH/YIELD from fresh typed local state. The independent oracle is separate source.

Formal seed: 137820260918001. Formal cases: 120,000, balanced across CLEAR_PROGRESS / UNCERTAIN_TRANSIENT / HARD_INVALIDATION. State-change offsets are sampled only from {2.5,7.5,12.5,17.5,22.5,27.5,32.5} ms. Reaction deadline = change + 12 ms.

Exactly one formal invocation, reruns/replacements/tuning0. A PASS does not authorize a classifier experiment by itself; if all exposed residuals are deterministic, parent disposition remains HOLD_DETERMINISTIC_LANE_SUFFICIENT.
