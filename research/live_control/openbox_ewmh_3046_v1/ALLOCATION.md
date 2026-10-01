 #3046 Openbox EWMH matrix allocation
Date: 2026-09-20 Asia/Tokyo
Image: mixed-formal-3025:20260920
Digest: sha256:c8fec4d7541b306b9266ce8d7800abad8e665e63d6ea1e5f62574d4b122a28d1
Network: disabled; one fresh container, two isolated displays.
Variants: standard Openbox (4 desktops) and explicit rc.xml (1 desktop, focusNew/focusLast/raiseOnFocus).
Result: HOLD_NO_EWMH_ACTIVE_WINDOW.
Both variants listed _NET_ACTIVE_WINDOW in _NET_SUPPORTED and exposed _NET_SUPPORTING_WM_CHECK, but root _NET_ACTIVE_WINDOW was not found. xdotool getactivewindow failed before/after activation; windowactivate returned rc=0 with property errors.
Source hash: 03254e876dca99d1398de548789dd7447d369daa001ac6d7f0203ab8d1aad417
Result hash: c0246670fe739e275d6e016ac2a0fc64c8b7a2173cdd1631117e6de8eb1eca74
