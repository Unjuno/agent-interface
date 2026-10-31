# WSLc preflight-included reverse-order comparison

One prospectively frozen reverse-outer-order replication of `wslc_model_three_arm_preflight_20261031_a03` used `gpt-6.1-sol` low, identical seed and WSLc Chromium workload, with arm and preflight order persistent/plain/ephemeral. Each arm had a separate fresh no-image schema preflight session before container startup; all three responses passed independent JSON Schema validation and reported usage. The direct-executable preflight is a successor path rather than the older schema_preflight_gate_v1.

All three arms independently submitted six exact tasks and all 18 task records verified release. Persistent followed cold/reuse/reuse/repair/reuse/reuse; the old reference was MISSING with zero old-reference pointer admissions before repair. All 17 call IDs were distinct, 14 task image hashes matched, and input scripts plus 2029 container and 2033 host source hashes matched after the run. Host and container exited zero; exact container inspect returned not found. ZIP integrity was verified.

| Arm | Preflight + grounding calls | Total input tokens | Cached input subset | Total output tokens | Task-time sum | Preflight duration | Sum of both |
|---|---:|---:|---:|---:|---:|---:|---:|
| Persistent | 1 + 2 | 36,869 | 12,288 | 421 | 23.573 s | 5.992 s | 29.566 s |
| Plain | 1 + 6 | 104,195 | 74,112 | 553 | 29.916 s | 5.417 s | 35.333 s |
| Ephemeral | 1 + 6 | 105,365 | 83,456 | 845 | 33.765 s | 6.277 s | 40.043 s |

Persistent used 64.62% fewer input tokens and its preflight-plus-task duration sum was 16.32% lower than plain in this run. The preceding preflight-included run showed 64.56% fewer input tokens but a 5.59% longer duration sum. These sequential samples suggest token savings in this fixture, while the observed time difference changes direction. Sums omit other setup and idle intervals, cached input is included in input, and cost is unknown. Fixed order, sample size, cache/thread effects and the non-hardened exploratory bridge limit inference; this does not establish a general speedup or close issue #57.

The archive preserves preflight answers/usage and separate schema checks, task exchanges, model-call outputs, container receipts, scripts and input inventories. Six host protocol journals contain local paths and remain locally retained; their hashes and sizes are recorded separately. No credentials were copied. The container client explicitly selects installed Chromium. Host source was independently hash-frozen for this run, unlike its predecessor.
