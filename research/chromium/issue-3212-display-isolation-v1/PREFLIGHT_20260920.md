# Bounded runtime preflight — 2026-09-20

Image: `mixed-formal-2992-debian:20260920`  
Network: `none`  
Display: `:99` (`Xvfb :99 -screen 0 1280x800x24 -nolisten tcp`)

The container launched Chromium 153.0.8010.47 with profile `/tmp/p1` and
CDP port 9222. CDP returned a browser websocket endpoint and the X11 query
returned a top-level window named `about:blank - Chromium` (XID `0x200003`)
plus the Chromium PID (`13`) and Xvfb PID (`9`). The process and display were
terminated after collection.

This is `PREFLIGHT_IDENTITY_CHANNEL_AVAILABLE`, not a formal effect result:
no input was dispatched, no DOM mutation was requested, and no generation
restart or stale-receipt control was exercised.
