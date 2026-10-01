# Issue #4219 — MotorState Inkscape pointer-effect transfer

Allocation: `motor-state-inkscape-effect-4219-20260923-01`.

## H
A command-only pointer state can continue a drag after an external pointer displacement and lose the intended Inkscape SVG effect. A fresh X-server observed MotorState should preserve a stable drag, refuse MISMATCH before button-down, and refuse UNKNOWN when observation is unavailable.

## T
Private Xvfb/Openbox/Inkscape 1.4; actual XTEST pointer/button events; one red SVG rectangle. Conditions: STABLE_NAIVE, DISPLACED_NAIVE, DISPLACED_OBSERVED_GUARD, STABLE_OBSERVED_GUARD, OBSERVER_UNAVAILABLE_NAIVE, OBSERVER_UNAVAILABLE_GUARD. Formal: 3 repetitions, one six-case batch per repetition, fresh Xvfb/app lifetime per case. Exact commands after GitHub source readback:

`python -B runner.py formal 0 formal-0`
`python -B runner.py formal 1 formal-1`
`python -B runner.py formal 2 formal-2`
`python -B audit.py formal-0/RAW.jsonl formal-1/RAW.jsonl formal-2/RAW.jsonl --out AUDIT.json`
`python -B test_audit.py formal-0/RAW.jsonl formal-1/RAW.jsonl formal-2/RAW.jsonl`

No retry, replacement, pooling or post-result tuning. Saved SVG bytes/geometry are scorer-only and never authorize input.

## D
PASS_MOTOR_STATE_POINTER_EFFECT_GUARD_SCOPED only with 18/18 complete: stable intended effect 6/6; DISPLACED_NAIVE MISMATCH + dispatched + intended-effect false 3/3; displaced guard MISMATCH refusals 3/3; UNKNOWN guard refusals 3/3; candidate wrong effect 0; every dispatched case observes Button1 held and every case finishes neutral; authority none; independent audit errors=[]; 10/10 corruptions rejected.

## C
Fixture geometry, selection state, X11 focus, drag threshold and Xvfb/Openbox behavior are scoped assumptions. A refusal trades liveness for correctness. X-server state is not physical HID telemetry.

## U
No model/planner usefulness, screenshot/token/latency benefit, natural displacement rate, arbitrary Inkscape document, second pointer application, cross-platform, runtime or product promotion.
