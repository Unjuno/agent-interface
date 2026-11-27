# WSLc real-model three-arm exploratory comparison

One prospectively frozen fixed-order six-task-per-arm run used `gpt-6.1-sol` low effort, the same seed, isolated WSLc Chromium image and checked runtime. The host handled model calls through a single-use shared-volume bridge; credentials stayed on the host. Each arm had its own persistent model thread. The schema preflight was **not run**, so this is an exploratory comparison and does not close issue #57. The bridge is not hardened against an adversarial container.

All three arms independently submitted six exact tasks; each of 18 task records verified input release. Persistent routes were cold/reuse/reuse/repair/reuse/reuse; on the changed layout the old reference was MISSING with zero old-reference pointer admissions before repair succeeded. Fourteen model requests and 14 unique responses were accounted for; request-image hashes matched. Host and container exited zero, exact container inspect reported not found, and all 2029 mounted source hashes matched. The raw archive passed ZIP verification.

| Arm | Grounding calls | Input tokens | Cached input subset | Output tokens | Sum of six task times | Sum of model-call times |
|---|---:|---:|---:|---:|---:|---:|
| Plain | 6 | 93,054 | 73,472 | 372 | 29.025 s | 19.821 s |
| Ephemeral | 6 | 94,505 | 75,136 | 706 | 33.925 s | 20.495 s |
| Persistent | 2 | 25,895 | 12,288 | 226 | 24.025 s | 8.330 s |

In this one fixed-order run, persistent task-time sum was 17.23% lower and input tokens 72.17% lower than plain. Cached input is included in input, not added to it; cost is unknown. Task-time sums do not include all setup or schema preflight, and the model-call time excludes some host/session overhead. Arm order, small sample, shared workload, cache and persistent-thread effects confound inference. This does not establish population reliability, a general speedup, production readiness or MAP01 completion.

The compressed archive preserves container outputs, all request/response/image exchanges, model-call results, conditions and scripts. The three host app-server journals contain local paths, so they remain locally retained; their hashes and byte counts are recorded separately. No credentials were copied. The mounted runtime source is pinned by the included 2029-file hash inventory; the client has an explicit Chromium path.
