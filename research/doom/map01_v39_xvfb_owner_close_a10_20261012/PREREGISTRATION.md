# A10 preregistration - exact current-main Xvfb owner close

**H.** V4->V3->V12 admits one key to a focused isolated Xvfb client; close emits matching KeyRelease, observer key-up, verified terminal owner_release and stopped owner thread.

**T.** One `a` press on Xvfb `:132`, then wrapper close and terminal verification.

**D.** PASS_METHOD_SCOPED if frozen source hashes match and raw audit confirms client event order/window/keycode, observer up, verified close receipt, stopped thread and Xvfb exit. Setup/incomplete trace STOP; complete mismatch FAIL. One candidate and one auditor.

**C.** Synthetic X-server only; no application/game/model/physical input/live lane.

**U.** No application consumption, useful feedback, latency distribution, threat response, recovery or task completion claim.

Base main: `f185a9059d485a4f8d5a65e9e7f6782897f67eae`.
