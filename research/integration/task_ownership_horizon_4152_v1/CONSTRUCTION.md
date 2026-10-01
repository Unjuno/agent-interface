# Excluded construction

- construction-01: STOP_SETUP_XAUTHORITY before any XTEST click. Xvfb socket and Tk ready file existed, but controller-side Python-Xlib used the container default `/opt/xvfb/.Xauthority` and raised `XauthError`. Formal rows: 0.
- correction: for the already private `Xvfb -ac -nolisten tcp` fixture, set controller-process `XAUTHORITY=/dev/null` as well as child environment. Scientific policy/schedule/gates unchanged.
- construction-02: PASS_EXCLUDED. Stable explicit horizon produced 3 effects and TASK_COMPLETE; invalidation explicit produced exactly 1 effect then OWNERSHIP_INVALIDATED while a separately evaluated current authority check remained admitted. Cooperative app exits0; pointer button1 neutral; Xvfb is intentionally SIGTERM-cleaned. 2 schedule tests plus 10 copied-evidence mutation controls pass. Formal rows remain0.
