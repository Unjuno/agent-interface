# Current-main WSLc per-key repeat-off caller diagnostic R09

Status: **DIAGNOSTIC / OLD TASK FAILED / PRODUCT HOLD**.

Both runs kept global auto-repeat enabled and verified the A key's per-key repeat bit off before the caller. Normal mode's unittest exited 0; XRes disconnect and release readback succeeded (release worker 1,474.36 ms, separate keymap neutral). The old task effect count increased 1→28 and its independent oracle failed; the delayed-A flag was true. A separate fresh-generation task passed without old-input contamination and the old fence stayed UNKNOWN. Optimized mode observed owner disconnect but the 1.5 s release worker timed out at 1,504.94 ms; A was down at readback and final fixture cleanup read all keys up.

Turning off only the A key's repeat bit also did not eliminate repeated effects in this caller harness. Do not compare R08/R09 effect counts as a controlled effect-size estimate: the one-shot runs differ in scheduling and recovery latency. Direct R10/R11 controls show the same Xvfb settings do suppress repeats in isolated XTEST probes, leaving the caller/harness interaction unresolved. No production setting or source changed.