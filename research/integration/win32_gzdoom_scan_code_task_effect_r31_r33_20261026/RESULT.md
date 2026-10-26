# GZDoom MAP01 scan-code task effect and matched caller replication (2026-10-26)

This record covers the later `win32_gzdoom_recovery_generation_task` R31 and `win32_gzdoom_w_forward_matched_caller_efficiency` R32/R33 series. These labels are distinct from the earlier `map01_native_windows` R31–R33 failed diagnostic.

## Question and change

The earlier native diagnostic produced no visible task effect using its key path. The Win32 backend and program contract were extended with an optional `scan_code` key encoding, retaining the existing virtual-key encoding as the default. The backend maps a virtual key with `MapVirtualKeyW(MAPVK_VK_TO_VSC_EX)`, emits scan-code `SendInput`, remembers the encoding while held, and uses the same encoding for explicit and terminal release.

The empirical question was whether this public compiled route could produce the configured `W=+forward` MAP01 effect and whether its caller path was faster than direct standard-MCP calls. The task oracle was independent of dispatch and bound success to the exact call, operation and target generation. Each new task used a fresh process/generation and exact cleanup. R32/R33 used two counterbalanced pairs each.

## R31 recovery-to-task result

- Pre-native-call held-SHIFT recovery and same-generation UP readback completed in 15 ms, below the frozen 3,000 ms limit.
- A stale-generation probe was refused before input. One compiled action sent scan-coded W down for 600 ms, explicitly sent W up, and called `release_all`.
- Public pixel effect was 54.3117%; the independent observer measured 54.5109%. The exact task oracle returned `task_success=true` for the expected call, operation and fresh generation.
- Release receipt and neutral readback passed; the exact GZDoom process exited 0 and foreground restoration passed. The post-action observation request began 1.8129 ms after dispatch response return by QPC.
- Frozen audit: 13/13 checks, 5/5 preregistration hashes and 47/47 raw hashes.

## R32/R33 matched caller-path result

Each arm performed the same configured W task with bounded pre-native recovery, stale-generation refusal, independent visual/oracle checks, release, and cleanup. Ordering was direct→compiled in pair 1 and compiled→direct in pair 2 for each series.

| Series / pair | Direct | Compiled | Compiled minus direct |
|---|---:|---:|---:|
| R32 pair 1 | 2.484 s | 2.594 s | +110 ms |
| R32 pair 2 | 2.532 s | 2.578 s | +46 ms |
| R33 pair 1 | 2.516 s | 2.562 s | +46 ms |
| R33 pair 2 | 2.484 s | 2.547 s | +63 ms |

All eight cells produced the required visible effect and exact independent task-oracle success, verified neutral input after release, and clean GZDoom exit. Public and independent effect fractions were all above 54%. The R32 originals retain their frozen 11/13 auditor results; the separately preregistered corrected R33 auditor passes all four R32 packets 16/16 and all four R33 packets 16/16. It corrects two field-path/count assumptions and does not rewrite the original audits. The eight raw manifests contain 368 entries and the preregistration manifests contain 48 entries; independent local rehash found zero mismatches.

Across four pairs, direct caller-path mean was 2.504 s and compiled mean was 2.57025 s. Compiled-minus-direct paired differences were +110, +46, +46 and +63 ms; the mean difference was +66.25 ms (+2.65%). Dispatch response averaged 1.47675 s direct and 1.48825 s compiled (+11.5 ms). The measured paths contain no model/provider call, so these are caller-path measurements, not end-to-end agent efficiency or token/cost measurements.

## Interpretation and limits

Scan-coded `SendInput` produced task effects through the tested Win32 public caller on this GZDoom/Freedoom MAP01 setup. This weakens the earlier Raw Input-only explanation for the no-effect trials. The experiment changed the key encoding and other run details; it does not isolate encoding as the sole causal difference or observe which keyboard backend the GZDoom process selected.

Four matched pairs and 4/4 task success per arm on one PC are descriptive, not a reliability bound or broad transfer result. The task is configured forward movement, not MAP01 completion. No model/provider economics, energy, or WSLc qualification is established. No WSLc or Docker was used. Older UNKNOWN GZDoom processes and prior failure outcomes were not modified.

Source/runtime provenance: the live runs used the exact runtime source frozen in the local R31/R32 preregistration records, including the scan-code patch copied into this change. R31 report and frozen audit, R32/R33 reports and rollup, plus raw packet manifests are preserved in the local `private-packets/win32_gzdoom_recovery_generation_task_20261026_r31/` and `private-packets/win32_gzdoom_w_forward_matched_caller_efficiency_20261026_r32/` and `_r33/` directories. Raw process and screenshot captures remain local-only.

Local verification of the integrated source patch ran the contract, Win32 integration and target-generation execution-guard suites: 68 tests passed normally and 68 passed with `-O`; `git diff --check` passed. This does not rerun or alter any live experiment.
