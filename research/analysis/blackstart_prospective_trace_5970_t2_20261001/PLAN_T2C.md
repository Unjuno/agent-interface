# Issue #5970 T2c — one-shot successor after file-path STOP

T2b's frozen runner received the app's arm acknowledgement in `run_v2/trace/tk/app_events.jsonl`, but polled the nonexistent sibling `run_v2/trace/app_events.jsonl`. It therefore timed out before dispatch; the retained raw action log has no `dispatch_request`. T2c corrects the app-log path in a new runner and uses a separate output directory. The T2 and T2b source and raw outcomes remain immutable.

## H / T / D / C / U

- **H:** The already-frozen serialized arm/ack protocol will record the dispatched Shift press and release as paired app/observer events with one explicit shared causal parent each.
- **T2c:** Verify and retain the two earlier pre-dispatch STOPs, then on a fresh Xvfb display run the hash-pinned archived app/observer as the same instrumented test copies. Poll the Tk stream at its actual `tk/app_events.jsonl` destination. Arm both sources before each of two XTest transitions; check same parent ID, distinct local event IDs/sequences, matching X event identity, and terminal neutral keymap. Candidate and independent audit each run once; no formal #4135 allocation is rerun.
- **D:** `PASS_PROSPECTIVE_CAUSAL_IDS` only if the two live transitions each produce exactly one complete, matching, explicitly parented observation in both sources after both acknowledgements and before no inferred timestamp edge; neutral terminal keymap required. Any mismatch or missing record is HOLD/FAIL as preregistered.
- **C:** This remains a serialized, isolated Xvfb/Tk instrumentation feasibility test. It does not cover concurrent/unprompted events, production telemetry, overhead, authority policy, or user benefit. Docker Desktop Linux engine remains unavailable; WSL2 Xvfb is the isolated host fallback.
- **U:** Production binding, concurrent event correlation, logger overhead, semantic truth, and recovery benefit remain open.
