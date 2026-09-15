# Plan — native X11 Xorg-dummy environment transfer v1

Dependency implementation: native tight-loop source freeze `48030f5829690bdd3209d05974e390d88e7742a9`, retained head `3f6e46556e44983d39e306a58ca80c688e7b2af5` / PR #145.

Question: does the strict-lowercase-ASCII 1 ms/character candidate remain exact when the compiled Go+cgo/X11/XTest tight-loop moves from Xvfb to X.Org Server 21.1.16 with the dummy video driver?

Formal order is fixed at `1,12 ms`. Each arm gets a fresh Xorg display, Openbox, isolated LibreOffice Calc profile and XLSX. The controller executes the same 16-string corpus as PR #145. A separate post-execution openpyxl process scores durable workbook values. Stale observation must inject zero events and terminal release must verify empty. 0 ms is not rerun and no Xorg-dummy 0 ms outcome is inferred.

PASS: both 1 and 12 ms are 16/16 exact and transport/stale/release controls pass. FAIL_1MS_TRANSFER: 1 ms is wrong while 12 ms is exact. FAIL_ENVIRONMENT: 12 ms or control gates fail.

No model/provider/network call. No WSLg/Wayland/Windows/macOS claim. Timing is fixture-local.
