# X11 absolute pointer relocation distance R1

Task `X11-ABSOLUTE-POINTER-RELOCATION-DISTANCE-R1-20260918-001` / Issue #1684.

## H
With the same private Xvfb, Python-Xlib/XTEST client, one absolute MotionNotify request, common reset point and XSync endpoint, varying only displacement over {1,8,64,256}px should have no material distance component at this fixture scale. PASS gates: class-median spread <=0.25ms and class-p95 spread <=0.75ms.

## T
100 balanced blocks; each block includes all four distances once in cyclically rotated order. Reset to center before every measured row; reset timing excluded. Measure perf_counter_ns immediately before fake_input through actor XSync return, then independently read root pointer from a second Xlib connection. 400 formal rows total. One private Xvfb allocation. Construction-only stepwise multi-request path is sensitivity control and is not pooled.

## D
PASS iff exact target400/400, neutral buttons400/400, exactly100 rows/distance, valid positive timing, median spread<=250000ns, p95 spread<=750000ns, formal1/reruns0 and independent audit/source integrity pass. Correctness pass but spread exceeded => HOLD_X11_DISTANCE_COMPONENT_EXPOSED. Readback/timing/cleanup error => FAIL_X11_RELOCATION_INTEGRITY.

## C
Xvfb/XTEST absolute motion may not model physical HID paths, Wayland, remote desktop or application hover semantics. XSync is server processing, not arbitrary application effect completion.

## U
No model/token/task/human-tempo/cross-platform claim.
