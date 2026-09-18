# Construction history — Issue #1728

No formal allocation was consumed during construction.

1. Policy-compatibility probe confirmed the parent #1711 failure mechanism: managed Chromium `URLBlocklist:["*"]` prevents the local-file task effect. A separate probe showed built-in `Ctrl+J` and `Ctrl+H` produce exact Downloads/History titles without network or URL input.
2. First #1728 integrated construction stopped at the focus-recovery step: Xlib `SetInputFocus` changed the X input focus ID but did not restore Chromium's WM active state, so `Ctrl+H` was not consumed. No complete scientific row was produced. Construction-only repair uses `wmctrl -ia` before `SetInputFocus`, matching #1711's explicitly allowed direct-WM recovery primitive.
3. The first complete integrated construction then passed all preregistered gates. It is summarized in `CONSTRUCTION_RESULT.json`; it is excluded from formal evidence.
