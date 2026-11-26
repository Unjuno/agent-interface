# Native Codex three-arm comparison for issue #57

On 2026-11-26 JST, the registered WSL2 comparison ran once using source commit `69a46db1a83c3080ea17b2d5e4ad3d766142848b`. The audit returned **RETAIN** for this six-task block. All 18 submissions were exact, all 123 accepted input programs had verified release, and all 17 provider calls reported the five usage fields.

| Arm | Exact submissions | Verified releases | Schema + grounding calls | Input tokens | Cached input | Cache-write input | Output tokens | Reasoning output |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Plain | 6/6 | 18/18 | 1 + 6 | 68,589 | 6,784 | 0 | 763 | 315 |
| Ephemeral | 6/6 | 48/48 | 1 + 6 | 69,240 | 6,784 | 0 | 1,112 | 307 |
| Persistent | 6/6 | 57/57 | 1 + 2 | 29,224 | 0 | 0 | 496 | 151 |

Cached input and reasoning output are already included in their respective input and output totals. The cumulative input totals include each arm's schema preflight. On this block, persistent first used fewer cumulative input tokens than both other arms at task 2. Its final input total was 57.4% below plain and 57.8% below ephemeral. At the task-4 layout change, the audit verified one old-layout MISSING check and zero button-down admissions between that check and fresh target revalidation.

## Registered conditions

- The three arms ran in fixed order, plain → ephemeral → persistent, using seed `991032` and the same Chrome form fixture, task sequence and target values. The layout was A for the first three tasks and B for the final three. Task 4 was the registered invalidation and repair point.
- Plain used per-task model-grounded coordinates. Ephemeral minted fresh grounded handles for each task. Persistent reused handles within a layout and grounded once at the start and once at the layout change.
- All three arms used `gpt-5.6-luna` at `low` reasoning effort on the Windows native Codex CLI `0.171.0-alpha.13.2`, with Chrome for Testing `156.0.8078.4` running in WSL2. Each arm had one owned App Server, with a fresh thread for each grounding call. The allocation allowed three schema preflights and fourteen grounding calls with no automatic retry.
- The supervisor and all three arms used isolated X11 sessions. The systemd service used `KillMode=control-group`, a 30-minute runtime limit and an 8-second stop timeout. The run ended with all four X11 sessions retired and all six Windows Jobs empty.

## Observed durations

| Arm | Schema preflight interval | Arm interval | Sum of six task durations |
| --- | ---: | ---: | ---: |
| Plain | 11.098 s | 36.639 s | 32.554 s |
| Ephemeral | 8.805 s | 44.805 s | 42.859 s |
| Persistent | 9.021 s | 29.378 s | 27.504 s |

The recorded interval from the first schema preflight's start to the final arm's end was 139.767 s. The arm interval includes setup and retirement within that arm. These durations cover one fixed-order run at one seed on one host. The result supports the registered token and call-count comparison for this fixture. General latency, pricing and reliability require separate measurements.

## Evidence and verification

[SUMMARY.json](SUMMARY.json) records the public conditions and aggregate observations. The registration and launch-plan hashes commit to the prospective conditions. The raw and host hashes commit to the locally held evidence manifests.

| Evidence | SHA-256 |
| --- | --- |
| Registration | `7ecb61fdaf6d617621b3ee8fe24e49445e55b20378bd98fe7675fecdc6c3a75c` |
| Launch plan | `538fdc7c8e8384d6e110d175330d11b226a7c8a1c6095731e33dcdddb90d07ac` |
| Raw seal, 792 files | `c9bd54e4a20760d644fade244ea887432229f63b00c0eb7cc76863b8fe803072` |
| Host seal, 9 files | `0cca8b210850be97b74c3567586c81ed959110fd0230c9507dfdc736d553224b` |

A separate read-only invocation of the [audit entry point](../../../runtime/native_comparison_cli_v1.py) reproduced the capture result byte for byte using the retained seals. An independent review verified the two seals and recounted all five usage fields across the 17 recorded calls. Reviewers with authorized access to the local corpus can pass the allocation and the launch, raw and host hashes to the `audit` subcommand at the recorded source revision. Public readers can inspect the method and recompute the comparison from the aggregates. Rechecking original provider messages, screenshots, input receipts and host custody requires the sealed local corpus.
