# #3038 Calc re-acquisition allocation
Date: 2026-09-20 Asia/Tokyo
Image: mixed-formal-3025:20260920
Digest: sha256:c8fec4d7541b306b9266ce8d7800abad8e665e63d6ea1e5f62574d4b122a28d1
Network: disabled; fresh container.
Change: after modal recovery, scan visible X11 windows and record xdotool name/xprop WM_CLASS before geometry.
Result: FAIL_MIXED_APP_LONG_SESSION; exit 1; event_count 22; checks [true,true,true,true,false].
Passed: focus drift, modal, geometry transition, Chromium replacement.
Failed: return-to-Calc active validation; activation/fallback report BadMatch for Calc XID 6291457.
Observation: reacquire scan did not expose a LibreOffice WM_CLASS; preserve uncertainty.
Source hash: formal_session.py c278d06f01f83d193fcd97870ed708bb2f924106fa53a87aa67e041f5d855f67
Result hash: 8a69a8e9bc2bc0c45a98bbdebcc6c12822721d9c5dd78a855ffca6cbf2a466e7
Model/network calls: 0/0
