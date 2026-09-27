# Generation renewal diagnostic — 2026-09-20

Image `mixed-formal-2992-debian:20260920`, Docker `--network none`.

Two independent X servers and Chromium profiles were started:

| generation | display | CDP | Xvfb PID | Chromium PID | top-level XID |
|---|---|---:|---:|---:|---|
| p1 | `:99` | 9222 | 10 | 14 | `0x200003` |
| p2 | `:100` | 9223 | 163 | 167 | `0x200003` |

Both CDP endpoints returned Chromium 153.0.8010.47 browser websocket URLs.
The same numeric XID was allocated by the two separate X servers. Therefore
an XID-only freshness check is unsound; the authoritative resource key must
include the display/server identity (and the correlated process/profile/CDP
generation). No input or DOM effect was dispatched.

Decision: `STOP_XID_ONLY_IDENTITY_UNSAFE`; this is a design diagnostic, not a
Chromium effect failure and not a live-control PASS.
