# Reverse-order native Codex comparison for issue #57

The reverse block ran once on 2026-11-26 JST at source commit `128feed3f6b3d1e3c4c20c79728b86b3be9e0ce4`. The audit returned **RETAIN**, with the same task-2 cumulative input break-even observed in the forward block. All 18 submissions were exact and all 123 accepted input programs had verified release.

| Execution order | Exact submissions | Verified releases | Schema + grounding calls | Input tokens | Cached input | Cache-write input | Output tokens | Reasoning output |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Persistent | 6/6 | 57/57 | 1 + 2 | 29,216 | 6,784 | 0 | 487 | 142 |
| Ephemeral | 6/6 | 48/48 | 1 + 6 | 69,220 | 27,136 | 0 | 1,120 | 315 |
| Plain | 6/6 | 18/18 | 1 + 6 | 68,569 | 13,568 | 0 | 756 | 308 |

All 17 provider calls reported all five usage fields. Cached input and reasoning output are included in their respective input and output totals. Cumulative input counts include the schema preflight. In the reverse block, persistent used 57.4% fewer final input tokens than plain and 57.8% fewer than ephemeral. The audit verified one old-layout MISSING check at task 4 and zero button-down admissions before fresh target revalidation.

## Matched conditions

Both blocks used seed `991032`, the same six tasks, the same Chrome form fixture, and the same three-preflight and fourteen-grounding call budget. Tasks 1–3 used layout A. Tasks 4–6 used layout B, with invalidation and repair at task 4. Both blocks used `gpt-5.6-luna` at `low` reasoning effort, Windows native Codex CLI `0.171.0-alpha.13.2`, and Chrome for Testing `156.0.8078.4` in WSL2. The blocks had fresh allocations, one owned App Server per arm, a fresh thread per grounding call, and no automatic retries. [Forward block](../native_three_arm_57_wsl_69a46db1_20261126/README.md)

The forward block ran plain → ephemeral → persistent. The reverse block ran persistent → ephemeral → plain using the source revision that registers and audits reverse order. The reverse run's four private X11 sessions retired and its six Windows Jobs ended empty. The systemd service used `KillMode=control-group`, a 30-minute runtime limit and an 8-second stop timeout.

## Forward and reverse observations

| Arm | Forward input | Reverse input | Forward cached input | Reverse cached input |
| --- | ---: | ---: | ---: | ---: |
| Plain | 68,589 | 68,569 | 6,784 | 13,568 |
| Ephemeral | 69,240 | 69,220 | 6,784 | 27,136 |
| Persistent | 29,224 | 29,216 | 0 | 6,784 |

Persistent used fewer input tokens and made fewer provider calls than either comparison arm in both blocks. The two runs used one seed and one fixture, with ephemeral in the middle both times. The reported cache counts differed across blocks. Fresh local threads and App Servers establish local session boundaries. Provider-side cache state and the effect of order alone are unresolved. General latency, pricing and reliability require separate measurements.

## Observed reverse durations

| Arm | Schema preflight interval | Arm interval | Sum of six task durations |
| --- | ---: | ---: | ---: |
| Persistent | 10.113 s | 30.411 s | 26.559 s |
| Ephemeral | 8.256 s | 50.864 s | 48.928 s |
| Plain | 8.754 s | 37.633 s | 34.388 s |

The interval from the first schema preflight's start to the final arm's end was 146.077 s for reverse and 139.767 s for forward. Each arm interval includes setup and retirement within that arm.

## Evidence and verification

The registration and launch-plan hashes bind the prospective conditions. The raw and host hashes bind the private retained evidence manifests. [Public summary](SUMMARY.json)

| Evidence | SHA-256 |
| --- | --- |
| Registration | `3ebde3b1e8e46518aef812737b28e30f15cf3c111c9a8915bce5352245b263b4` |
| Launch plan | `3e14c86061e546871350809187535d58bb1f3e329933b215f1b2c5d951816716` |
| Raw seal, 751 files | `81a3288480291a1447767063d1f842daec60dedbf1ba5f8a65e0f924a67edccf` |
| Host seal, 9 files | `ca53db61237c9ca49d1945a9d494832efb6ddd1ac5d292029552c62e215407f1` |

An independent review verified both manifests and recounted all five usage fields across the three schema preflights and fourteen grounding calls. The separate read-only audit reproduced the original result byte for byte. Public readers can inspect the audit method and recompute the comparison from the aggregates. Rechecking original messages, screenshots, input receipts and host custody requires the sealed local corpus at the recorded source revision. [Audit entry point](../../../runtime/native_comparison_cli_v1.py)
