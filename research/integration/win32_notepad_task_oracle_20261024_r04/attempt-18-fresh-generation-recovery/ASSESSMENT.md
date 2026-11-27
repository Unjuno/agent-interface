# R18 assessment — held-keyup recovery on the R17 target generation

**Outcome: `PASS_SCOPED_BOUNDED_RECOVERY`; independent postflight: `PASS_POSTFLIGHT`.** Preflight confirmed the R17 target HWND 370739280 remained visible, enabled and foreground, with blank document, SHIFT-up and target generation `3e0505c367c9faf8aac8133e4620a9d1de06ce481d487eb7265906286406888f`. This differs from R16 and shares the R17 PID/creation time and GUI thread. Public observation retained the R17 generation.

The production supervised-Win32 owner/producer path issued a real SHIFT-down. The isolated producer then blocked after the native down call returned and before invoking native `SendInput` for SHIFT-up. An independent native read observed SHIFT-down during the hold. One public cancellation was accepted as pending; the operation then reached terminal `recovered`, the producer exited with code -15, cancellation release was confirmed, and replay remained denied.

The retained owner interval from cleanup request to release acceptance was 16.000 ms at the coarse monotonic clock and 17.211 ms with `perf_counter_ns`; the 3 s cleanup deadline margin was 2.984 s. The independent same-generation key-state read found SHIFT-up, the document remained empty, and no emergency release was needed. A separate Python process after MCP close also confirmed the same generation, empty document and SHIFT-up. Task success remains null because this was a recovery-only program. The MCP close receipt's `release_confirmed=false` is retained; it is not used as the positive release evidence.

## Scope limit

This is one fresh-target-generation recovery sample at the backend-send boundary before the SHIFT-up API call. It is not a block inside Windows `SendInput` or the kernel, and does not establish arbitrary platform-I/O bounds, process-restart transfer, general reliability, task completion, stdio behavior, MAP01, matched efficiency or WSLc behavior. R13/R14 remain same-fixture repeated evidence; R18 extends that scoped condition to R17's distinct HWND/thread.
