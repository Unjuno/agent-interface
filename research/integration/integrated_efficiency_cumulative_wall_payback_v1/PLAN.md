# Integrated cumulative wall payback v1

Task `INTEGRATED-EFFICIENCY-CUMULATIVE-WALL-PAYBACK-20260917-001`, Issue #922.

H: charge each arm's retained preflight at task0, then append the exact six retained task elapsed intervals. Persistent is slower than plain after task1, crosses below plain at task2, stays below plain through task4 repair and task6, and stays below ephemeral from task1. Wall break-even vs plain is task2.

T: exact retained rows only; integer nanoseconds; source-first freeze; formal once; independent recomputation; corruption controls. No model/GUI/live/task input.

D: PASS only if source identities, final totals, task order/routes, cumulative relations and exact task2 wall payback all hold. HOLD if retained rows cannot support exact reconstruction; FAIL on claim/integrity mismatch.

C/U: one posthoc retained allocation only. This is descriptive cumulative wall accounting, not population speed, local/model time attribution, monetary cost, human tempo, second-domain evidence or extrapolation past six tasks.
