# Issue #4297 — XGrabServer liveness / owner-death recovery result

**Disposition: `PASS_X11_SERVER_GRAB_LIVENESS_BOUNDARY_SCOPED`**

Allocation `x11-server-grab-liveness-20260924-01` ran exactly once after public source/gate freeze. Formal rows 15/15; reruns/replacements/post-result tuning 0/0/0. Independent audit: 174 checks, errors=[]; copied-evidence corruption controls: 12/12 rejected.
Postformal raw reconstruction audit-v2 independently re-derived case summaries from observer round trips, owner events and XSERVER_EXIT without using ROWS.json for the scientific decision: 690,719 checks, errors=[]; 12/12 raw-file corruption controls rejected. This strengthens evidence integrity only and did not rerun any formal case.

## Formal result

Three fresh private Xvfb lifetimes per condition:

| condition | max spanning observer stall, ms (r0/r1/r2) | observed grab-to-release/death boundary, ms | next post-release observer completion, ms |
|---|---|---|---|
| NO_GRAB | n/a | n/a | n/a |
| HEALTHY_1MS | 1.661 / 1.838 / 1.625 | 1.448 / 1.485 / 1.392 | 0.045 / 0.046 / 0.039 |
| HEALTHY_20MS | 21.771 / 20.803 / 20.730 | 21.516 / 20.579 / 20.498 | 0.275 / 0.113 / 0.092 |
| KILL_OWNER_20MS | 23.750 / 23.919 / 28.623 | 23.541 / 27.453 / 35.620 | 0.097 / 0.024 / 0.040 |
| HUNG_OWNER_100MS_WATCHDOG | 105.908 / 106.137 / 104.714 | 107.564 / 107.420 / 107.602 | 0.072 / 0.022 / 0.062 |

Every non-baseline case retained pre-grab, grab-spanning and post-release/death observer round trips. `HEALTHY_20MS` spanning stalls exceeded matched `HEALTHY_1MS` stalls in all three repetitions. Healthy owners exited0 after explicit `XUngrabServer`; kill/watchdog owners exited -9 without explicit ungrab. In all six externally killed cases, the already-running Xvfb remained alive at scoring and unrelated observer round trips resumed without X-server restart. All 15 Xvfb sockets were absent after owned cleanup.

The `NO_GRAB` rows had maximum observed round-trip durations 8.713 / 0.308 / 0.942 ms. That 8.713 ms baseline outlier is important: the study does not attribute every measured millisecond to XGrabServer and does not derive a production latency SLO. The discriminating evidence is the directed blocking/release boundary and owner-death recovery, not raw timing precision.

## H/T/D/C/U interpretation

**H supported at this scope.** An X server grab stalls an unrelated connected client while held. Explicit ungrab restores service. Killing the grab-owning client also restores service without restarting Xvfb. A live hung owner keeps the server-wide liveness hazard until an independent watchdog kills that client.

**T:** private Xvfb, Python-Xlib0.15, one owner and one independently connected continuous observer per case. No model/provider/network/user desktop/task input. Five fixed conditions x three repetitions. Observer was connected before each grab. Owner import/connection was completed before observation measurement so construction startup could not consume the measurement window.

**D:** all preregistered finite gates passed; independent raw audit errors=[]; 12/12 coherent corruptions rejected. Formal runner/audit/controls exits0 and stderr empty.

**C:** timings include scheduler/process/socket overhead. Supervisor process-death observation makes the 20 ms kill boundary substantially longer than exactly20ms in two repetitions. Continuous `Display.sync()` is deliberately aggressive. SIGKILL recovery is X-client disconnect evidence only; it is not power-loss evidence.

**U:** no natural hang probability, production latency budget, arbitrary Xorg/compositor/remote-X transfer, Wayland/Windows/macOS, physical HID, model/planner utility, token/image benefit or broad GUI correctness.

## Integration decision

The #4266 `XGrabServer` critical section has a real server-wide liveness cost. The private-Xvfb result shows owner death releases the grab, but a live hung owner can hold unrelated clients until externally terminated. Therefore production adoption cannot treat a successful grab as self-bounding: it needs an independently enforced bounded owner/watchdog or a different mechanism that provides the required check/use atomicity without an unbounded server-wide grab. This experiment does not choose between those architectures.
