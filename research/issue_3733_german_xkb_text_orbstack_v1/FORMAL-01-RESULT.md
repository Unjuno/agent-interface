# Formal-01 result — Issue #3733

## Disposition

**STOP_ENVIRONMENT_OR_SETUP.** The allocation did not send candidate text or any XTEST event, so it is not a PASS or FAIL for German formula delivery.

The exact-main source and frozen OrbStack image launched one fresh private Xvfb. XKEYBOARD/XTEST were present; the server and baseline core map were US. The single preregistered `setxkbmap -layout de` returned 0, server dump/query changed to German, and the client core-map fingerprint changed. Before invoking the candidate, the harness tried to find the `xev` receiver window. The frozen parser required `Outer window` and `Inner window` on separate lines, but this image emitted both IDs on one line. It stopped at `XEV_WINDOW_ID_TIMEOUT`.

The retained `xev.log` contains only the two window IDs. There are no KeyPress/KeyRelease records, no candidate plan, and no candidate backend emission. The raw is preserved unchanged; the failure is a runner defect.

Independent audit result: `STOP_ENVIRONMENT_OR_SETUP`; 0 integrity errors; exact candidate source and all 8 retained formal artifact files verified; 4/4 corruption challenges rejected. Raw SHA-256: `c2de5a3851881e5935cbdba94f798b1338f0e578d021bb184ea22c808a28f6de`.

The row's original Xlib connection also reported US `equal`/`asterisk` levels after the server transition. Formal-02 uses a new Xlib connection after applying the layout, preventing stale client cache from entering the candidate gate. Both corrections are frozen in the successor preregistration; formal-01 is not retried or relabeled.
