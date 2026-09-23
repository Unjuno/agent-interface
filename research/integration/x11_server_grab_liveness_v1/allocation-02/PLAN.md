# #4297 XGrabServer liveness / owner-death recovery

Allocation `x11-server-grab-liveness-4297-20260924-01`.

## H
An active XGrabServer blocks unrelated X round trips until ungrab or client disconnect. Healthy authored hold should bound the block; SIGKILL of the owner should release the server grab without restarting Xvfb; a live hung owner remains blocking until an independent watchdog terminates it.

## T
Private Xvfb, no task input/model/network. Conditions NO_GRAB, HEALTHY_1MS, HEALTHY_20MS, KILL_OWNER_20MS, HUNG_OWNER_100MS_WATCHDOG ×3 fresh Xvfb lifetimes =15. Observer performs GetInputFocus round trips before/during/after. For grab conditions, observer emits `observer_started` after the owner grab is confirmed; only then does the authored 1/20ms hold or 20/100ms supervisor timer begin. This synchronization is measurement plumbing, not an extra task action.

## D
PASS only with 15/15 complete rows, observer exit0, Xvfb alive through scoring, healthy during-request spanning ungrab and at least 80% of authored hold, HEALTHY_20MS > HEALTHY_1MS in every matched repetition, owner SIGKILL exit -9 and observer recovery after supervisor kill in kill/watchdog cases, raw-only audit errors=[], and >=10 corruption controls rejected. Complete contradiction is FAIL. Missing denominator/process/timing evidence is STOP/HOLD.

## C
Stall includes scheduling/socket overhead. SIGKILL tests X-client disconnect semantics in private Xvfb only. Watchdog adds architecture/process cost.

## U
No production SLO, natural hang probability, physical HID, other display systems, model/task/token/product claim.
