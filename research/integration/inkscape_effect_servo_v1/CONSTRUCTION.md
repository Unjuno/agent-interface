# Excluded construction history

- `construction_OPEN_LOOP`, `construction_MID_EFFECT_SERVO`, `construction_SERVO_OBSERVER_UNAVAILABLE`: all stopped before application science at `XVFB_NOT_READY`. The Xvfb/auth child setup existed, but the parent Python-Xlib connection did not inherit the case-local `XAUTHORITY`. These are retained setup STOPs, not scientific rows.
- `construction2_*`: changed only parent-process environment propagation. Three disjoint-offset `(8,5)` cells completed once. OPEN_LOOP observed effect `(22,13)` at pointer `(30,18)` and saved `(42,25)` at pointer `(50,30)`. MID_EFFECT_SERVO used the same `(22,13)`, residual `(28,17)`, moved once to pointer delta `(58,35)` and saved `(50,30)`. Observer-unavailable released/YIELD at `(30,18)` and saved partial `(22,13)`. All three ended input-neutral; Inkscape expected SIGTERM -15, Openbox/Xvfb 0.

Construction is excluded from the 12-case formal denominator and uses an offset not in formal.
- Pre-freeze test invocation from outside the study directory failed before tests with `ModuleNotFoundError: audit`; the receipt is retained as `UNIT_FIRST.stderr`. The invocation was corrected to run from the study directory without changing scientific source or gates, then all three pure unit methods passed.
