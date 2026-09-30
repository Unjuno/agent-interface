# Issue #4297 — XGrabServer liveness and owner-death recovery

Allocation: `x11-server-grab-liveness-20260924-01`
Branch: `research/x11-server-grab-liveness-20260923`
Additive path: `research/integration/x11_server_grab_liveness_v1/**`

## H
An active X server grab blocks unrelated clients' X round trips until explicit ungrab or owner disconnect. A healthy bounded hold should produce a bounded foreign-client stall; SIGKILL of the grab-owning client should release the grab without restarting Xvfb. A live hung owner remains a liveness hazard until an independent watchdog terminates it.

## T
Private fresh Xvfb per case; one independent owner process and one independent observer process. Observer connects before the grab and continuously issues `Display.sync()` round trips. Conditions, three repetitions each: `NO_GRAB`, `HEALTHY_1MS`, `HEALTHY_20MS`, `KILL_OWNER_20MS`, `HUNG_OWNER_100MS_WATCHDOG`. Healthy owner explicitly ungrabs. Kill/watchdog owner remains connected with the server grab until supervisor SIGKILL at the frozen 20/100 ms boundary. No model/provider/network/user desktop/task input. Formal command once: `python3 -B run.py --out formal-01 --reps 3`.

Construction is excluded. Two early construction attempts failed to overlap observer traffic with the grab because owner import/connection happened after the observer's fixed measurement window. The corrected construction arms/connects the owner before observer measurement and uses a file trigger only after observer readiness. Construction-04 passed 5/5 cases, independent audit, two unit tests, and 12/12 copied-evidence corruption controls. No formal row was consumed.

## D
`PASS_X11_SERVER_GRAB_LIVENESS_BOUNDARY_SCOPED` only if all 15 rows are retained; each non-baseline has pre/post responses and at least one request spanning the grab; healthy authored holds/stalls meet the frozen lower-support checks; matched 20 ms stall > 1 ms stall in all three repetitions; owner-kill and watchdog rows resume after process death without Xvfb restart; 100 ms watchdog and 20 ms kill boundaries are actually exposed; all observers exit0; Xvfb is alive at scoring; no socket remains after cleanup; independent audit errors=[]; 12/12 frozen corruption controls reject. Missing denominator/process/timing evidence is STOP/HOLD; complete contradictory behavior is FAIL.

## C
Round-trip stall includes scheduling, X socket transport and measurement overhead. SIGKILL tests private-Xvfb client-disconnect semantics, not power loss or arbitrary X servers. Watchdog termination is an explicit architectural cost. Continuous `Display.sync()` is an aggressive observer workload chosen to expose the boundary, not a natural desktop polling rate.

## U
No production latency SLO, natural hang probability, Wayland/Windows/macOS transfer, physical HID, planner/model benefit, token/image reduction, broad GUI correctness or product claim. This study does not rerun or modify #4266's Calc correctness result.
