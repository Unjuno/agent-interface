# Standard-caller Xvfb trial R02

Status: `PARTIAL_NORMAL_PASS_OPTIMIZED_HOLD`.

The corrected runner uses the CI variable `AGENT_INTERFACE_XVFB_PID`. The normal attempt exited 0 with captured Xvfb provenance, XRes disconnect, and an independent release readback. The old synthetic task's effect count grew from 1 to 4 by the delayed-request horizon; its task oracle failed. The separate fresh-session task oracle passed, the old cancellation remained UNKNOWN, and replay remained denied.

The single optimized attempt exited 1: the XRes supervisor returned UNKNOWN after its 150 ms query budget (`supervision_timeout`), so no release attempt was admitted by that path. Final container cleanup read all keys up. See R03 for three additional frozen optimized repetitions and R04 for the separate timing diagnostic.
