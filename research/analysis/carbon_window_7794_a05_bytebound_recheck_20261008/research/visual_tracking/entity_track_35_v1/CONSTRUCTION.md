# Excluded construction record

No formal case was executed in these attempts.

1. construction-01: STOP_XAUTHORITY_UNAVAILABLE before fixture/capture.
2. construction-02: capture/policy ran, but XTEST click mapping used the wrong X11 translation direction; no task effect.
3. construction-03: switched to retained canvas root origin, but asynchronous Tk event processing was not serviced while stdin blocked; no task effect.
4. construction-04: changed pointer movement to root warp + XTEST press/release; same event-loop blockage, no task effect.
5. construction-05: state command services pending Tk events; target click produced exactly one T movement by +18 y, wrong effect false, terminal X key/button state neutral. PASS_CONSTRUCTION.

These engineering attempts are excluded from the formal denominator and did not change formal scenarios or decision gates.
