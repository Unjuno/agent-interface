# Current-main WSLc XTEST repeat microcontrol R10

Status: **SCOPED CONTROL PASS; NO PRODUCT CLAIM**.

Six fresh WSLc/Xvfb containers (normal and `-O` Python × default, global autorepeat off, A-key per-key repeat off) each held one synthetic A press for 1,200 ms, then issued one release. Under default settings, both interpreters observed 15 A KeyPress and 15 A KeyRelease events. With global autorepeat off, both observed exactly 1 press/1 release. With only the A key repeat bit off, both observed exactly 1/1. An independent X client read A up after release in all six runs.

This validates that the pinned Xvfb/XTEST microcontrol responds to both repeat controls in an isolated single-key hold. It neither tests the standard caller's delayed-request path nor explains why R08/R09 still saw repeated A effects. All output, event timestamps, host commands and conditions are preserved.