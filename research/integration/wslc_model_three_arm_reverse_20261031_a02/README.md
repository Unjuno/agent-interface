# WSLc real-model three-arm reverse-order replication

One preregistered reverse-order replication of `wslc_model_three_arm_exploratory_20261031_a01` used `gpt-6.1-sol` low effort, the same seed, image, checked runtime and task workload. Arm order changed from plain/ephemeral/persistent to persistent/ephemeral/plain; each arm had its own persistent model thread. Schema preflight was **not run**. This is exploratory evidence and does not close issue #57. The shared-volume bridge is not hardened against an adversarial container.

All three arms independently submitted six exact tasks; all 18 task records verified input release. Persistent routes were cold/reuse/reuse/repair/reuse/reuse; its old reference was MISSING with zero old-reference pointer admissions before repair succeeded. All 14 request images matched, all 14 call IDs were unique, all 2029 mounted source hashes matched, host and container exited zero, and exact container inspect returned not found. Raw ZIP integrity was verified.

| Arm | Grounding calls | Input tokens | Cached input subset | Output tokens | Sum of six task times | Sum of model-call times |
|---|---:|---:|---:|---:|---:|---:|
| Persistent | 2 | 25,895 | 12,288 | 226 | 23.784 s | 8.253 s |
| Ephemeral | 6 | 94,365 | 74,752 | 678 | 36.235 s | 22.701 s |
| Plain | 6 | 93,134 | 81,920 | 388 | 29.496 s | 20.113 s |

In this run, persistent task-time sum was 19.37% lower and input tokens 72.20% lower than plain. The predecessor's corresponding values were 17.23% and 72.17%. These two sequential samples reverse the outer arm positions, but ephemeral remains in the middle; caching, thread continuity and sequence effects remain confounders. Cached input is a subset of input. Cost is unknown; task-time sums omit some setup and all schema preflight. This is not a population-level or production-speed estimate.

The archive preserves requests, images, responses, model-call results, container receipts, conditions and scripts. Host app-server journals contain local paths and remain local; their hashes and sizes are retained. No credentials were copied. The source hash inventory records 2029 mounted files; the client explicitly selects installed Chromium.
