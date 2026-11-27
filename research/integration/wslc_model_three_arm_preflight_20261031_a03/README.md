# WSLc real-model comparison including schema preflight

One prospectively frozen exploratory six-task-per-arm run used `gpt-6.1-sol` low effort, the same seed and isolated WSLc Chromium workload as the two preceding comparisons, with arm order ephemeral/plain/persistent. Before starting the container, each arm made a fresh no-image app-server schema-compatibility turn in a separate session; all three completed, reported usage and passed a separate JSON Schema validation. This is a successor preflight path using the current direct executable, not the older `schema_preflight_gate_v1` implementation. It grants no GUI authority.

All three arms independently submitted six exact tasks, and all 18 task records verified input release. Persistent followed cold/reuse/reuse/repair/reuse/reuse; its old reference was MISSING with zero old-reference pointer admissions before repair. The three preflight and 14 task turns had 17 distinct call IDs; 14 task image hashes matched, all 2029 mounted source hashes matched, both host and container exited zero, and exact container inspect returned not found. The raw archive passed ZIP verification.

| Arm | Preflight + grounding calls | Total input tokens | Cached input subset | Total output tokens | Task-time sum | Preflight duration | Sum of both |
|---|---:|---:|---:|---:|---:|---:|---:|
| Ephemeral | 1 + 6 | 105,505 | 59,904 | 873 | 35.738 s | 5.604 s | 41.342 s |
| Plain | 1 + 6 | 103,955 | 73,728 | 450 | 24.260 s | 5.062 s | 29.322 s |
| Persistent | 1 + 2 | 36,841 | 12,288 | 393 | 24.148 s | 6.814 s | 30.961 s |

Persistent used 64.56% fewer input tokens than plain including preflight, but its preflight-plus-task duration sum was 5.59% longer in this run. The sums omit other setup and idle intervals; they are not total end-to-end elapsed time. Cached input is included in input, not added to it; cost is unknown. Fixed order, one run, cache/thread effects and a non-hardened experimental bridge limit the inference. Do not claim a general speedup or close issue #57 from this record.

Raw archive includes preflight answers and usage, independent JSON Schema checks, 14 task requests/responses/images, model-call outputs, container receipts and conditions. Host protocol journals contain local paths and remain locally retained; their hashes and sizes are recorded separately. Credentials were not copied. The mounted client explicitly selects installed Chromium; exact input source hashes are recorded. The host adapter source was not independently hash-frozen before this trial, so source lineage remains a qualification boundary.
