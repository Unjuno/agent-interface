# Native pending-OS-I/O recovery and fresh task — R10–R12 (2026-10-26)

This consolidated index preserves three one-shot attempts as separate outcomes. The fault was a real overlapped `ConnectNamedPipe` request that remained kernel-pending after a real SHIFT-down and before the producer's SHIFT-up `SendInput`. It was not an API call hung inside `SendInput`.

## Preserved outcomes

| Attempt | Bounded release/recovery | Fresh task | Timing gate | Frozen/additive disposition |
|---|---|---|---|---|
| R10 | 15.000 ms helper monotonic / 16.5672 ms QPC; same-generation release/readback passed | Fixture click/type/save and exact oracle passed | Required fresh post-dispatch observation check failed | Frozen audit `audit_pass=false`; do not call the full protocol a pass |
| R11 | 16.000 ms helper monotonic / 16.000 ms QPC; same-generation release/readback passed | Stopped before action; zero action calls | Not measured | Observation wrapper passed an MCP envelope where a decoded body was expected; additive follow-up preserves the failure |
| R12 | 16.000 ms helper monotonic / 16.900 ms QPC; same-generation release/readback passed | Fresh compiled click/type/save; exact independent oracle passed | QPC request start was 2.6185 ms after dispatch response | Frozen audit 14/14 PASS |

All three recorded a pending overlapped connect (`ERROR_IO_PENDING` 997) and an unsignaled completion event (`WAIT_TIMEOUT` 258) before cancellation. R10's other task/release/oracle checks passed, but its post-dispatch observation gate failed. In addition, its conditions field `runtime_source_manifest_sha256` is `0afb9f71094eb39e34f09318333f920af30a8f23c4655a8b797ebd0ed4591592`, while the retained `runtime-source-manifest.json` currently hashes to `af1bd7ed77b79761d062554d3db48d4d7f9b76873da91a5566d32c93bf406991`. The discrepancy is preserved as a provenance limitation; no value was rewritten.

R12's exact task oracle `00f9ad28bd2f4fbc93ace8ba1dabe2e1` bound success to the action call, operation and fresh generation. It refused the retired generation before input, verified release and neutral native state, and passed graceful exit and foreground restoration. Dispatch response returned at perf-counter ns `680012169408300`; the next public observation request began at `680012172026800`. Its coarse monotonic capture-start tick tied the dispatch-return tick; strict ordering is supported by the separate QPC request timestamps.

## Independent byte and source checks

Independent local rehash of the frozen manifests found no file mismatches:

- R10: 39/39 raw entries and 5/5 pretrial entries.
- R11: 30/30 raw entries and 5/5 pretrial entries.
- R12: 39/39 raw entries and 5/5 pretrial entries.

R12's retained 220-file runtime source manifest hashes to `30644f6a5fa678b86eef9dc92b965ef1bdd819e85cd69f437d1e889ee9d09588`, matching the result record. Its trial used source commit `c31a2dedcfae2c3ed402c2f79b6df18982edf85a` plus the frozen dirty scan-code patch. That scan-code patch is now on main via PR #9590. Current main additionally has a later empty-obligation observation helper change in `runtime/cli_v1/win32_supervisor_helpers.py` and its test, which was absent from R12's frozen source; R12 does not validate that later helper behavior.

## Scope

R12 establishes one bounded supervisor recovery result for a pending overlapped named-pipe operation and one exact-generation task continuation on the recorded same-PC source. It does not prove a hard release bound for arbitrary OS/kernel/API hangs, a hang inside `SendInput`, broad reliability, MAP01 completion, provider/model economics, energy, or WSLc qualification. R10 remains a failed overall gate and R11 a task-stage harness failure. No WSLc or Docker was used. Full raw packets, screenshots and process captures remain local-only under the corresponding `private-packets/win32_native_blocked_osio_recovery_20261026_r10`, `_r11`, and `_r12` directories.
