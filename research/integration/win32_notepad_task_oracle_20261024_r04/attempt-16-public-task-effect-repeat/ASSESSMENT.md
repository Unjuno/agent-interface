# R16 assessment — repeated public-caller task effect

**Outcome: `PASS_TASK_EFFECT_AND_TIMING_SCOPED`; independent postflight: `PASS_POSTFLIGHT`.** The preregistered standard supervised-Win32 caller executed one exact text task on HWND 24840738. The preflight passed: the window was visible, enabled and foreground; the document was blank; SHIFT was up; and the target generation was `ff2b6086b6d8dcff988483ce4294eb3962d5864a0941b0e50bd820d8a120636a`. The public observation retained that generation.

The public `interface_dispatch` call entered `AI-CTRL-20261024-R16` through the `gap_ms=25` compiler path. Its terminal action completed with 40 input emissions and `release_confirmed=true`. The standard dispatch receipt leaves `task_success=null`; the separate exact-call native oracle returned `verified`, `task_success=true`, and `outcome=success` after reading the exact token and matching generation. Replay remained denied.

The separately dispatched select-all/backspace cleanup completed with `release_confirmed=true`; its exact-call oracle verified the empty document. A fresh standalone read after MCP close confirmed the same target generation, empty text and SHIFT-up. The MCP `close` receipt itself reports `release_confirmed=false`; this is retained as such and is not used as the release proof. The action receipts plus standalone postflight provide the positive release evidence.

## Timing

All task intervals use `perf_counter_ns`: dispatch start to first non-empty observation was 796.292 ms; dispatch start to first exact-token observation was 1,294.127 ms; dispatch start to terminal dispatch return was 1,416.601 ms. The polling loop sampled every 10 ms. These are scripted observation boundaries, not physical key latency or model inference/perception time. No model/provider was called.

## Repeatability and limits

R15 and R16 both passed this fixed task on the same Notepad target generation with the same `gap_ms=25` program shape. This is 2/2 conditional fixture outcomes, not an independent-sample or general reliability estimate: both share one host, process generation, target and caller. It supplies no fresh-generation transfer, stdio transport, API-internal blocked-I/O recovery, matched efficiency comparison, MAP01/game transfer or WSLc evidence.

The first R16 runner launch failed before preflight because the repository root was missing from `PYTHONPATH`; `runner-start-failure.json` preserves that setup failure. It dispatched no input. The frozen experiment then ran once with the repository root explicitly set.
