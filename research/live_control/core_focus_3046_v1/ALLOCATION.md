 #3046 X11 core-focus control allocation
Date: 2026-09-20 Asia/Tokyo
Image: mixed-formal-3025:20260920
Network: disabled; fresh container, two Openbox displays.
Result: PASS_CORE_FOCUS_ONLY (narrow observation only).
EWMH getactivewindow failed and _NET_ACTIVE_WINDOW was not found on both displays. xdotool getwindowfocus returned rc=0 with XID 2097675 before/after activation, but that XID is the Openbox WM surface, not Calc XID 1293. Therefore core focus is measurable but does not validate target activation.
Source hash: 0a5112e49932d1dd29c8f8603686799c1ed6cf424748b54ffe193d23c1b869ec
Result hash: f585df32c18a3991394f64803321d9fbd7d1f6161364d9a450272ae692300ff5
