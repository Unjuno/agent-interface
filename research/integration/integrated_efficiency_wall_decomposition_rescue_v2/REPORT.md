# Retained wall decomposition rescue v2

Issue #929, task `INTEGRATED-EFFICIENCY-WALL-DECOMPOSITION-RESCUE-20260917-002`.

Decision: **PASS_RETAINED_WALL_DECOMPOSITION_RESCUED_SCOPED**. Formal invocation exactly 1, reruns 0. Independent audit PASS with errors `[]`; six corruption controls reject 6/6. The source-first archive was published and read back before formal, repairing #847's source-materialization blocker without consuming #847's original formal0/1 allocation.

## Decomposition

| arm | phase-complete wall ms | retained model-stage ms | unattributed remainder ms | model-stage share | local obs | durable calls |
|---|---:|---:|---:|---:|---:|---:|
| plain | 62754.198912 | 47176.820803 | 15577.378109 | 75.18% | 105 | 36 |
| ephemeral | 80378.859099 | 55587.244764 | 24791.614335 | 69.16% | 129 | 96 |
| persistent | 51627.109593 | 22650.049495 | 28977.060098 | 43.87% | 136 | 114 |

For persistent minus plain: total wall `-11127.089319 ms` = model-stage `-24526.771308 ms` + remainder `+13399.681989 ms` exactly. For persistent minus ephemeral: total wall `-28751.749506 ms` = model-stage `-32937.195269 ms` + remainder `+4185.445763 ms` exactly.

Thus, in this retained six-task Chromium allocation, the persistent path's lower phase-complete wall coexists with a much smaller retained model-associated envelope and a larger **unattributed** remainder. The decomposition is arithmetic, not subsystem attribution.

## Interpretation boundary

`retained_model_stage_ms` is the retained task image-model wait envelope plus preflight model-subprocess lifetime; it is not pure provider generation latency. `unattributed_remainder_ms` contains whatever retained wall is not assigned to those model-associated intervals and must not be called `local_time`. Local observation and durable-call counts are shown only descriptively with `timing_attribution=false`; this experiment does not infer per-call cost, money, energy, causality, population speedup, or future-horizon behavior.
