# WSLc real-model comparison on a modified fixture

One preregistered exploratory six-task-per-arm run used `gpt-6.1-sol` low, seed 771903 and changed both A/B layout margins, the page heading, field label and submit label relative to the preceding fixed fixture. The same modified fixture was used for all arms in fixed order plain/persistent/ephemeral. Before container startup each arm made a fresh no-image schema preflight in a separate session; all three answers passed independent JSON Schema validation with usage recorded. This tests one changed browser fixture, not a second application domain.

All 18 task submissions were independently exact and all 18 task release records verified. Persistent followed cold/reuse/reuse/repair/reuse/reuse; the old reference was MISSING with zero old-reference pointer admissions before repair. All 17 call IDs were distinct, 14 task image hashes matched, and the six input files plus 2029 container and 2033 host source hashes matched after the run. Host and container exited zero; exact container inspect returned not found. ZIP integrity was verified.

| Arm | Preflight + grounding calls | Total input tokens | Cached input subset | Total output tokens | Task-time sum | Preflight duration | Sum of both |
|---|---:|---:|---:|---:|---:|---:|---:|
| Plain | 1 + 6 | 104,075 | 74,112 | 494 | 28.122 s | 7.262 s | 35.385 s |
| Persistent | 1 + 2 | 36,841 | 12,288 | 396 | 23.296 s | 6.290 s | 29.586 s |
| Ephemeral | 1 + 6 | 105,365 | 75,136 | 846 | 32.835 s | 5.794 s | 38.630 s |

Persistent used 64.60% fewer input tokens and its preflight-plus-task duration sum was 16.39% lower than plain in this run. Sums omit other setup and idle intervals; cached input is included in input and cost is unknown. Fixed order, one modified fixture, cache/thread effects, and a non-hardened exploratory bridge limit inference. This does not establish a general speedup, broad GUI reliability, second-domain performance or completion of issue #57.

The raw archive includes the changed fixture source, preflight answers and schema audit, all task exchanges, model-call outputs, container receipts, conditions and input inventories. Six host protocol journals contain local paths and remain locally retained; their hashes and sizes are separately recorded. No credentials were copied. The mounted client explicitly selects installed Chromium.
