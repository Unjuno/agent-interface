# #3042 LibreOffice active-window micro allocation
Date: 2026-09-20 Asia/Tokyo
Image: mixed-formal-3025:20260920
Digest: sha256:c8fec4d7541b306b9266ce8d7800abad8e665e63d6ea1e5f62574d4b122a28d1
Network: disabled; fresh container.
Scope: Xvfb :142 + Openbox + LibreOffice Calc only; no model/network calls.
Result: HOLD_NO_ACTIVE_WINDOW_CONTRACT.
Observed Calc candidate XID 1293 geometry 1600x1000. windowactivate returned rc=0 and windowfocus rc=0, but xdotool getactivewindow failed every time with _NET_ACTIVE_WINDOW property error; xprop -root _NET_ACTIVE_WINDOW reported not found. Do not infer active success from command rc.
Initial source hash: 778f9b59a6cd448230331d9d72cb98dd40325148d67daab145caee4e3bdc2a96
Result hash: c85d043164ca91e312bbd98f66deb28fc4d90a7008fe1a37faf22ebe60e2cda3
