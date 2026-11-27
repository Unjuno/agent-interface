# MAP01 public observation ROI probe (2026-11-14)

## Question

Can the public Win32 MCP observation API confirm the exact same target generation with a 1×1 `screen_physical_px` capture faster than the 1520×825 region used during R170 recovery observation?

## Conditions and result

The probe used the merged-main source tree `bee6da37915ff79f781fe83a0ab9318b813d58f7`, one freshly launched native GZDoom MAP01 process (PID 60256, HWND 282330920), and 16 public stdio `interface_observe` calls. Eight sequential pairs alternated full-client region `[200,139,1520,825]` and one-pixel region `[202,141,1,1]`. No `interface_dispatch` call was made. All 16 observations returned `status=returned`, `target_generation_consistency=matched`, the same target-generation digest, and the expected PNG dimensions. QPC timestamps bracketed each complete client call.

| Capture | Samples (ms) | Median | Nearest-rank p90 |
|---|---|---:|---:|
| 1520×825 | 350.008, 341.897, 337.711, 348.028, 336.715, 346.371, 340.026, 349.038 | 344.134 | 350.008 |
| 1×1 | 32.405, 22.861, 28.321, 21.281, 14.317, 22.275, 15.718, 28.013 | 22.568 | 32.405 |

The one-pixel capture reduced this observation-call median by 93.4% (321.566 ms) and nearest-rank p90 by 90.7% (317.603 ms) in this single process. This supports a candidate optimization for generation-only revalidation during recovery. It does not establish a recovery-latency improvement until exercised inside the integrated exception/recovery path.

## Adjudication and limits

The 16-call measurement window passed its capture and generation checks. After those calls, a Computer Use click intended to close the app landed in the game client; the refreshed screenshot showed ammo 49 whereas the pre-probe HUD showed 50. The click and ammo change are temporally associated, but the exact OS event sequence was not captured. Accordingly the **overall attempt is `DEVIATION_AFTER_MEASURED_CALLS`, not a clean zero-input PASS**. Immediately before a normal `WM_CLOSE`, the mouse-left and W keys read UP; the exact HWND/PID/executable matched, and the process exited without forced termination. No public MCP dispatch or recovery was run.

This probe does not test expiry, delayed input, physical input release, recovery, task-effect verification by the controller, reliability, WSLc, or controller-level speed/economics. The timing readings remain usable for the completed observation calls, but must not be presented as an integrated control result. The local private packet preserves 96 files with zero manifest mismatches; its manifest SHA-256 is `af56926eadf1b1c362811840d1d83dbaf22e3c0134f7931fbb953f274776178e`.

## Next discriminating check

In a separately frozen native exception-recovery attempt, replace only the recovery-time generation revalidation capture with the 1×1 public observation. Keep the original full-resolution independent effect captures, exact-generation binding, UNKNOWN/no-replay policy, release readback, and both two-second horizons. Accept only if the integrated timing meets its unchanged bound and all release/effect gates pass; otherwise preserve the failure.

Public conditions, all 16 timing/image-hash rows, summary, and their hashes are in this directory. `SHA256SUMS.json` hashes the committed Git blob bytes (Git normalizes these text files to LF); the task-local manifest independently hashes exact private-packet bytes. Full raw MCP receipts and PNGs remain in the task-local packet.
