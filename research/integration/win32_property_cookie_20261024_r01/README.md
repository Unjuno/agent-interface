# Win32 cross-process window-property lifetime probe R01

This no-input feasibility probe used a spawned child process to own one hidden
`STATIC` HWND. The parent read the production Win32 owner identity, set a
unique `SetPropW` value on that foreign-process window, and read the exact
value back. The child destroyed the window and created another on the same
PID and GUI thread. The old HWND was no longer valid, the stale-handle property
read returned zero, and the new HWND had no property value. The numeric HWND
was different, so same-number reuse behavior was not exercised. The owned
child exited with code 0 and was not forcibly terminated; no window was
activated and no input was sent.

The frozen result is `CROSS_PROCESS_PROPERTY_WORKS_NO_REUSE_OBSERVED`; the
independent structural audit passes 9/9. This shows that this same-integrity
parent could attach and read a per-window marker on a child-owned HWND, and
that the marker was absent on the new, different HWND. It does not prove that
an HWND-incarnation cookie will be accepted for every target, or that it
distinguishes same-number reuse. It does not test elevated/UIPI-restricted
targets, application compatibility, target atomicity, input, release,
recovery, task effect, MAP01, efficiency, or reliability.

Microsoft documents that `SetPropW` is subject to UIPI and can set properties
only on windows owned by processes at equal or lower integrity. It also says
applications should remove properties they add before `WM_NCDESTROY`. Those
limits make this a candidate requiring fail-closed availability handling and
an explicit cleanup design, not a production implementation. See
[SetPropW](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-setpropw)
and [About Window Properties](https://learn.microsoft.com/en-us/windows/win32/winmsg/about-window-properties).

`conditions.json` was frozen before the run. `raw.json` preserves all values
and process events. `audit.py` recomputes structural claims from raw;
`SHA256SUMS.txt` records file hashes.
