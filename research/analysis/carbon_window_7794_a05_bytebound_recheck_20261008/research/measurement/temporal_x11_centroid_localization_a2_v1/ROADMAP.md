# TEMPORAL-X11-CENTROID-LOCALIZATION-A2-20260918-009

Issue #1326. Direct predecessor #1312 stopped before science because the parent Python-Xlib client inherited an invalid XAUTHORITY path.

Only harness change: runner sets its own DISPLAY and XAUTHORITY before Display().
Science stays #1312: private 320x200x24 Xvfb/Tk, saturated red 12x24 rectangle, authored fractional x, 7.3 px paired displacement, raw root XGetImage y=100 scanline, red-pixel centroid, 4 formal sessions, phases 0.00..0.99, directions + - + -, 400 pairs/800 frames.

Formal budget: one supervisor invocation, reruns0.
