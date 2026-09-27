# R7 formal outcome — Issue #4763

Allocation: `visual-temporal-570-stale-contour-r7-20260927-01`. Frozen source/input set: `37d2c5cdc4beb50560dfddcd9a8c91a4bade5487b480e6d214a2abac5601ed12`. Formal calls: 36/36; retries: 0; failures before response: None.

## Decision

`HOLD_AUDIT_OR_GPU`. Independent networkless audit errors: response_schema:screen-05-stale_contour. This is a HOLD, not a hypothesis result, because `screen-05-stale_contour` returned `present=false` with a non-null box, violating the frozen response contract. No calls were repeated and the raw response remains unchanged.

## Per-arm outcomes

| Arm | Positive hits | Absent abstentions | Mean normalized center error | Stale-location selections |
|---|---:|---:|---:|---:|
| CURRENT_RAW | 0/10 | 2/2 | 0.771053 | 0 |
| PAIRED_HISTORY | 0/10 | 2/2 | 1.000000 | 0 |
| STALE_CONTOUR | 0/10 | 2/2 | 1.000000 | 0 |

All 36 calls had overlapping GPU sampler evidence above baseline (162 overlapping samples total). The 12/12 pinned-container construction tests and preformal input audit passed. The RTX 3080 container and R7 internal Docker network were removed by the launcher; the separate R3 container remained untouched.

The 35 schema-valid calls repeatedly abstained on positive cases, with three `CURRENT_RAW` exceptions returning the same off-target box; no arm reached IoU≥0.5. Since the independent audit is HOLD, these values are descriptive only and do not support a clean comparative or temporal-effect claim.

No retry, seed replacement, prompt change, or post-freeze tuning occurred. Follow-up work requires a distinct successor Issue and allocation.
