# Integrated cumulative wall payback v1 — retained first outcome

Decision: **`PASS_CUMULATIVE_WALL_PAYBACK_RECONSTRUCTED_SCOPED`**.

All values below include each arm's retained schema-preflight wall time before task 1. This is a posthoc reconstruction of one retained six-task allocation, not a new live speed sample.

| Task | Persistent route | Plain cumulative (s) | Ephemeral cumulative (s) | Persistent cumulative (s) | Persistent − plain (s) | Persistent − ephemeral (s) |
|---:|---|---:|---:|---:|---:|---:|
| 1 | cold | 15.752336766 | 20.426462942 | 18.520781079 | 2.768444313 | -1.905681863 |
| 2 | reuse | 24.778643634 | 31.363326369 | 22.449437518 | -2.329206116 | -8.913888851 |
| 3 | reuse | 33.682320339 | 42.457295786 | 26.752597378 | -6.929722961 | -15.704698408 |
| 4 | repair | 42.809466296 | 55.013936751 | 39.094062535 | -3.715403761 | -15.919874216 |
| 5 | reuse | 53.309688542 | 67.754765283 | 44.831649574 | -8.478038968 | -22.923115709 |
| 6 | reuse | 62.754198912 | 80.378859099 | 51.627109593 | -11.127089319 | -28.751749506 |

Wall break-even versus plain: **task 2**.
Wall break-even versus ephemeral: **task 1**.
Retained token break-even: **task 2** (same task number, independent metric).
Task-6 persistent lead vs plain: **11.127089319 s**; vs ephemeral: **28.751749506 s**.

Interpretation: persistent pays a cold wall premium versus plain at task 1, repays it by task 2, and remains cumulatively ahead after the task-4 invalidation/repair and through task 6. Persistent is cumulatively ahead of ephemeral from task 1. This does not identify causal subsystem latency or extrapolate beyond the frozen horizon.

Formal invocation: 1; reruns: 0. Independent audit PASS; five structured corruption controls all rejected.
