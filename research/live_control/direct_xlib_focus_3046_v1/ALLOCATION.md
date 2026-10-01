 #3046 direct Xlib focus allocation
Date: 2026-09-20 Asia/Tokyo
Image: mixed-formal-3025:20260920
Network: disabled; fresh container.
Scope: Xvfb + Openbox + LibreOffice Calc; direct Xlib XSetInputFocus to the discovered Calc XID.
Result: HOLD_DIRECT_FOCUS_NOT_OBSERVED.
Target Calc XID 1293; XSetInputFocus returned 1 (failure), core focus remained Openbox XID 2097675, and EWMH getactivewindow failed. Geometry visibility does not imply an input-focusable top-level surface.
Source hash: 07055c0380517b64b0c217a2f31b930ac01fe7e502f79576d04ca6ab9eb3cb1d
Result hash: 6f7fb8f0c3d5e4b2a8ac48575ee5602f6618b166e47c0880195b6452e7dbabe3
Model/network calls: 0/0
