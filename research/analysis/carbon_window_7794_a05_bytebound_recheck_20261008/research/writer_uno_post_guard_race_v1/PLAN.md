# Writer UNO post-guard TOCTOU v1

H: the retained Writer bound-prefix checks are not atomic with subsequent XTest input; a state change after the final guard can cross the proof boundary.

T: real private Xvfb/Openbox/LibreOffice Writer. A starts `book`, B `bookk`, desired A `bookkeeperoffice`. Bind exact A URL+RuntimeUID to XID and pass final active/focus plus exact UNO UID/text guard. Then, strictly after recording guard pass and before first input, run one of: no fault, activate B, mutate A text to `boox`. Reacquire Ctrl+End and send unchanged suffix without another guard. Separate UNO process reads A/B after effect. Retain monotonic guard/fault/first-input timestamps.

D: no-fault exact; focus fault must demonstrate wrong-target effect; text fault must demonstrate stale-effect write. All physical input empty. The experiment proves a schedulable boundary, not natural probability or a product fix.

C/U: deterministic hook widens the gap. Private X11 Writer only. No atomicity/platform/general reliability claim.
