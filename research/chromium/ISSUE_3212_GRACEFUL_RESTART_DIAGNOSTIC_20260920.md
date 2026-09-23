# Issue #3212 graceful-restart diagnostic — 2026-09-20

Additive diagnostic following `STOP_GRACEFUL_RESTART_ALLOCATION_TIMEOUT`; no prior record is changed.

## H/T/D/C/U

- H: The graceful-restart stop may be caused by X11 resource discovery retaining the old window rather than by Chromium/CDP startup failure.
- T: One Docker `--network none` allocation with Xvfb and real Chromium. After p1 termination, p2 was launched with a new profile and CDP port; the existing strict ready gate required both a new X11 main-window XID and CDP `document.readyState=complete`.
- D: At timeout, CDP port `9223` returned `document.readyState="complete"`, while X11 discovery returned only the excluded old primary window `4194307` (`primary=[('4194307','')]`). No new XID was admitted, and no input/effect was dispatched under an uncertain binding.
- C: `STOP_GRACEFUL_RESTART_X11_DISCOVERY_OLD_RESOURCE`. This is a runner/resource-identification failure, not evidence of browser effect failure. The strict gate correctly stopped instead of reusing the old XID.
- U: Enumerate all mapped Chromium windows after p2 launch, correlate the CDP target to an X11 process/window identity, and require a fresh XID before retrying the graceful-restart effect.

## Raw diagnostic

```json
{"p2_cdp_ready":"complete","p2_x11_primary":[["4194307",""]],"excluded_old_xid":"4194307","new_xid":null,"dispatch":false,"formal_decision":"STOP_GRACEFUL_RESTART_X11_DISCOVERY_OLD_RESOURCE"}
```
