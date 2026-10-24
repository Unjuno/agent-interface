# R17 assessment — fresh target generation through the standard caller

**Outcome: `PASS_TASK_EFFECT_AND_TIMING_SCOPED`; independent postflight: `PASS_POSTFLIGHT`.** The first post-launch snapshot returned no additional Notepad window, so the frozen selector stopped without input. A later fresh app inventory found one additional HWND, 370739280, after the single app-ID launch. It was the only new returned Notepad window; Computer Use inspected and activated that exact blank window. The initial no-input observation remains in `launch-stop.json` and `INITIAL_STOP_RESULT.json`; the later discovery and selection are recorded separately.

Preflight confirmed HWND 370739280 visible, enabled and foreground, with one supported edit child, blank text and SHIFT-up. Its target generation was `3e0505c367c9faf8aac8133e4620a9d1de06ce481d487eb7265906286406888f`, distinct from R16 `ff2b6086b6d8dcff988483ce4294eb3962d5864a0941b0e50bd820d8a120636a`. Read-only owner identity comparison found the same Notepad PID 18100 and process creation time as R16, but a different HWND and GUI thread. Therefore this qualifies distinct target-generation propagation, not a fresh process restart.

The standard supervised-Win32 public MCP observation retained the R17 generation. One `gap_ms=25` text task entered `AI-CTRL-20261024-R17`; dispatch completed with 40 emissions and `release_confirmed=true`. The standard dispatch receipt kept `task_success=null`. A separate exact-call native oracle verified the same-generation exact token with `task_success=true` and `outcome=success`; replay was denied.

A separate select-all/backspace cleanup completed with `release_confirmed=true` and exact-call task verification of the empty document. The MCP close receipt reports `release_confirmed=false` and remains so in raw. After close, an independent process verified the same R17 generation, empty text and SHIFT-up.

## Timing

Using `perf_counter_ns`, dispatch start to first non-empty observation was 802.139 ms; to first exact-token observation, 1,304.756 ms; and to terminal dispatch return, 1,428.292 ms. Polling was approximately every 10 ms. These are scripted observation boundaries, not physical input latency or model inference/perception time. No model/provider or stdio path was used.

## Scope

R17 advances target-generation propagation through the standard caller for a different HWND and GUI thread in the same Notepad process. It does not prove behavior after process restart, arbitrary stale-target races, API-internal blocked-I/O release, broad reliability, matched efficiency, MAP01/game transfer or WSLc. The launcher’s delayed new-window appearance is part of the retained condition; no existing document was substituted.

The runner printed its complete PASS summary, but the initial stop `RESULT.json` was not replaced by the runner on disk. The current structured `RESULT.json` reconstructs that summary from captured console output and exact raw MCP/oracle files. The original no-input result is retained separately.
