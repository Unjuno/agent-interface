# R15 — exact task effect and observation timing through public Win32 caller

## Outcome

**PASS_TASK_EFFECT_AND_TIMING_SCOPED.** Before input, the target HWND 24840738 was enabled, visible and foreground; its blank `RichEditD2DPT` child, SHIFT-up state, and generation `ff2b6086b6d8dcff988483ce4294eb3962d5864a0941b0e50bd820d8a120636a` were confirmed. Public observation retained that generation. The standard in-process MCP caller dispatched one `gap_ms=25` text program; its completed action receipt reported 40 input emissions and verified release. An exact-call independent oracle then read the native Notepad document and same target generation, returning `verified`, `task_success=true`, outcome `success`. No model/provider call was made.

A separate cleanup program selected all, deleted the token, and returned release-confirmed; its exact-call oracle verified the empty document. After the MCP session closed, a fresh standalone native read confirmed the same generation, SHIFT-up, and empty document.

## Timing

All interval values use `time.perf_counter_ns()`:

- Dispatch start to first non-empty document observation: 771839800 ns (771.840 ms).
- Dispatch start to first exact-token observation: 1270426200 ns (1270.426 ms).
- Dispatch start to terminal dispatch return: 1385103300 ns (1385.103 ms).
- First exact-token poll to independent task-oracle read: 116206200 ns (116.206 ms).
- Terminal dispatch return to oracle read: 1529100 ns.

The independent poll ran every 10 ms while dispatch remained pending. These are dispatch-to-observation boundaries, not exact physical input latency or model perception/inference time. The first exact read bounds when the effect was observed, not when it first occurred.

## Scope and limits

This is one deterministic scripted task on one existing Notepad window via the public MCP interface and in-process server. It confirms standard-caller task effect and observation timing for this fixture. It does not use stdio transport, a model/provider, a fresh process generation, a saved file, an efficiency baseline, MAP01, or WSLc; it does not estimate general reliability. `interface_close.release_confirmed=false` is a separate close receipt; both task action receipts and the independent postflight show neutral input state.

## Evidence

`preflight.json`, `run_task_effect.py`, public observe/dispatch/verify/cleanup/close requests and reports, `oracle-log.json`, `RESULT.json`, and `postflight.json` preserve the input conditions, exact calls, independent reads and timing. The parent packet `SHA256SUMS` covers these files.
