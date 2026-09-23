# Issue #3212 forced-restart diagnostic — 2026-09-20

Additive diagnostic; prior graceful-restart STOP and all scoped PASS records remain unchanged.

## H/T/D/C/U

- H: If graceful `terminate()` leaves the old X11 resource, an explicit process kill plus an X11 destruction barrier may expose a fresh resource for safe rebinding.
- T: One Docker `--network none` allocation with real Chromium/Xvfb. After p1 valid setup, the runner used `p1.kill()`, waited for process exit, waited up to 5 seconds for old XID `4194307` to disappear, then launched p2 with a new profile/port and required CDP ready plus a non-old XID.
- D: The old XID remained visible with `_NET_WM_PID=132` after the kill/barrier. P2 CDP reported `document.readyState="complete"`, but X11 discovery returned only `[('4194307','',132)]`; no new XID was admitted and no p2 input/effect was dispatched.
- C: `STOP_FORCED_RESTART_X11_RESOURCE_PERSISTENCE`. Stronger process termination did not resolve the identity problem. This is not evidence of Chromium effect failure or restart safety.
- U: Inspect the Xvfb/Chromium process tree and X11 window lifecycle directly, or use a new isolated X display/server per allocation; only then retry new-generation effect binding.

## Raw diagnostic

```json
{"termination":"SIGKILL","old_xid":"4194307","old_xid_pid":132,"p2_cdp_ready":"complete","x11_primary":[["4194307","",132]],"new_xid":null,"dispatch":false,"formal_decision":"STOP_FORCED_RESTART_X11_RESOURCE_PERSISTENCE"}
```
