# #3040 usable Calc surface allocation
Date: 2026-09-20 Asia/Tokyo
Image: mixed-formal-3025:20260920
Digest: sha256:c8fec4d7541b306b9266ce8d7800abad8e665e63d6ea1e5f62574d4b122a28d1
Network: disabled; fresh container.
Change: wait for a visible candidate with geometry >=100x100 before registering Calc capability.
Result: FAIL_MIXED_APP_LONG_SESSION; exit 1; event_count 23; checks [true,true,false,true,false].
Calc candidate: XID 1293, geometry 1600x1000.
Failed: geometry transition had identical old/new geometry; return-to-Calc active validation failed despite bounded activation fallback.
Evidence: xdotool/xprop scan did not identify LibreOffice WM_CLASS; activation emitted _NET_WM_DESKTOP timeout and fallback active mismatch.
Source hash: formal_session.py 829f6aee6efe9352b73c95e0860989781bc95a4a994b61aa28121e27bc15fcb4
Result hash: 3b87ae42f7fa78e7f9e7e0d3b6c7d0c6f0edae97c75449b296a61b469ed5eac5
Model/network calls: 0/0
