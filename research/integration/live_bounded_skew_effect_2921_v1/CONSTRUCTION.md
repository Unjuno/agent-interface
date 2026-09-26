# Construction history — Issue #2921

Formal rows/invocations: 0/0 throughout. No #1594 formal row was rerun or pooled.

1. construction-01 — `STOP_XAUTHORITY_CONTROLLER_ENV` before task input. Private Xvfb used `-ac`, but the controller process inherited a missing default Xauthority path. Repair: propagate only `DISPLAY` and `XAUTHORITY=/dev/null` to the controller.
2. construction-02 — `STOP_XTEST_TEXT_ENCODER` before Return/effect. The bounded construction encoder lacked `>`; repair added only `>` = Shift+period.
3. construction-03 — 12 fresh xterm sessions completed, but the initial independent oracle duplicated the XID-based identity and was blind to application replacement. Retained as `STOP_ORACLE_REPLACEMENT_BLIND`; not scientific evidence.
4. construction-04 — changed only scoring/raw truth by retaining old/current xterm PIDs and requiring same application process in the independent oracle. The #1594 `candidate`/`strict` functions, 2 ms budget, schedules and task-input policy were unchanged. This construction exposes a live same-XID replacement alias and stops formal allocation.

Construction-04 disposition: `HOLD_LIVE_TRANSFER_UNSAFE_REPLACEMENT_ALIAS / STOP_BEFORE_FORMAL`.
