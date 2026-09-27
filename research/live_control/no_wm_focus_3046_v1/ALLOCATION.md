 #3046 no-WM focus control allocation
Date: 2026-09-20 Asia/Tokyo
Image: mixed-formal-3025:20260920
Network: disabled; fresh container, two Xvfb displays with no WM.
Result: HOLD_NO_ACTIVE_WINDOW.
Calc XID 1293 geometry 1600x1000 was visible. EWMH atoms were absent as expected; xdotool activation/getactivewindow failed. getwindowfocus reported XGetInputFocus focused window 1 and BadWindow, not Calc. This excludes a usable no-WM core-focus fallback for this harness.
Source hash: f704d88935142f62fd4d6872e29e7d7dd54c83c6a04311033c19128d4227ce43
Result hash: 54b53d4566d40f74f056cb76fd63d55a2721ea4d9cd6d904e3ad45a1fdf0c61f
Model/network calls: 0/0
