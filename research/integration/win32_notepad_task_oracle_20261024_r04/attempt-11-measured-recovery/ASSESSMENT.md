# R11 — retained recovery timing on the current standard caller

## Outcome

**PASS_SCOPED_BOUNDED_RECOVERY.** A new local Windows attempt used the public in-process MCP server functions with the production supervised-Win32 owner, recovery and independent observer helpers. The only injected fault was a hold in the producer after the real `SendInput(SHIFT-down)` call returned.

Preflight bound the same Notepad generation `ff2b6086b6d8dcff988483ce4294eb3962d5864a0941b0e50bd820d8a120636a`; the document was empty and SHIFT was up. During the hold, an independent native state read observed SHIFT down. `interface_cancel` initially returned pending. The later dispatch and `interface_results` both retained the action and cancellation as recovered, with release confirmed and replay denied; the producer exit code was -15. Independent post-recovery state read observed SHIFT up for the same generation, and bounded `WM_GETTEXT` confirmed the document remained empty.

The retained owner timestamps were:

- cleanup request: 531699625000000 ns
- recovery/readback confirmation: 531699640000000 ns
- reported cleanup latency: 15000000 ns (15 ms)
- configured cleanup deadline: 531702625000000 ns
- recorded margin to deadline: 2985000000 ns

The status contract sets `recovered` only after matching release and neutral-readback receipts arrive before the cleanup deadline. The final `recovered` state therefore establishes the configured deadline gate for this sample.

## Timing qualification and limits

On this Python 3.11 Windows host, `time.monotonic_ns()` reports implementation `GetTickCount64()` with 0.015625 s resolution. The 15 ms interval is effectively one coarse clock tick and is not a precise recovery-latency estimate. The R11 harness did not bracket these exact boundaries with `perf_counter_ns()`; do not retrofit or infer a higher-resolution duration from unrelated timestamps. The follow-up timing instrumentation adds a separate high-resolution interval for future attempts while retaining monotonic deadline evidence.

This is one recovery-only sample. It does not test a hang inside the Windows API, arbitrary platform I/O, stdio transport, task success, MAP01, efficiency, or reliability. No WSLc or Docker allocation was used. `close.release_confirmed=false` is a separate close result, not a contradiction of the terminal action/cancellation release receipts.

## Evidence

`preflight.json`, `observe.json`, `dispatch-after-cancel.json`, `results.json`, `cancel.json`, `close.json`, the two MCP call directories, `observe-1.png`, and `RESULT.json` preserve the call and native observations. `run_measured_recovery.py` is the R11 harness. The root packet `SHA256SUMS` includes these files.
