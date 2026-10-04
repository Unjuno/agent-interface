# Mode-flap diagnostic T0 A02 — Issue #7505

Status: formal allocation disposition `HOLD_AUDIT` because frozen auditor v1 detected a candidate alarm-map encoding defect. Post-run raw replay v2 independently reconstructed the missing alarms and found the method gate `FAIL_METHOD_SCOPED`: mode-flap warned on all held-out flicker episodes but was later than queue, margin, and CUSUM comparators. A01 stopped before candidate process creation and was not retried. See [RESULTS.md](RESULTS.md), [EXECUTION.md](EXECUTION.md), and the [A01 STOP record](../mode_flap_7505_t0_a01_20261004/STOP.md).

This package evaluates whether explicit source-bound service-mode transition history adds pre-loss warning signal in a deterministic discrete-event fixture. It cannot affect scheduling, route choice, observation, input, or control. The six families are endogenous flicker, demand drift, noisy single-mode telemetry, policy oscillation without service loss, abrupt failure, and stable service.

Read [PREREG.md](PREREG.md) for frozen H/T/D/C/U, comparator definitions, thresholds, outcome criteria, and execution limits. `candidate.py` emitted the event ledger; `audit.py` is the frozen auditor v1; `audit_v2.py` is a supplemental post-run raw replay that does not alter the candidate output.

This is a finite synthetic method result only. It does not establish a warning for a real verifier, computer-control runtime, service, or user task; it estimates no operational false-alarm rate and authorizes no damping or control response.
