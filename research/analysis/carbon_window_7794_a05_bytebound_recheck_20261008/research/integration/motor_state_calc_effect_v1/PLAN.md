# Issue #27 — MotorState Calc application-effect rung

Allocation: `motor-state-calc-effect-27-20260923-01`.

## H
After a valid Calc focus receipt, an external focus transfer can make a command-only continuation type into the wrong surface. A fresh X-server focus observation should detect the mismatch and refuse before task input. If the observer is unavailable, the candidate should return UNKNOWN/refuse rather than convert missing evidence into confirmation. Stable current-focus cases should still complete the intended Calc A1 effect.

## T
Provided Linux execution container, LibreOffice Calc 25.2.3.2, private Xvfb and Python-Xlib/XTEST. The task action path is XTEST only. A read-only evaluator connects to LibreOffice's local UNO socket after the action and reads A1; it never authorizes or emits task input. A separate Tk Entry fixture is the wrong-surface sink in focus-transfer cases and writes its received text to a scorer file.

Three scenarios x two policies x three repetitions = 18 fresh Calc/X-server lifetimes: STABLE, FOCUS_TRANSFERRED, OBSERVER_UNAVAILABLE crossed with NAIVE_COMMAND and OBSERVED_GUARD. Each case first exposes a held Shift key and verifies neutral release. Then the treatment either types `7` + Return or refuses. Stable: both policies should write Calc A1=`7`. Focus transferred: naive should type `7` into the helper and leave Calc blank; candidate should REFUSE_MISMATCH with no task input/effect. Observer unavailable: naive acts from stale command evidence and happens to write Calc A1=`7`; candidate should REFUSE_UNKNOWN. This last cell is a liveness cost, not a correctness win.

Excluded construction is retained separately. Formal is three immutable six-case batches, rep0/rep1/rep2, one invocation each, no retry/replacement/tuning.

## D
`PASS_MOTOR_STATE_EFFECT_GUARD_SCOPED` requires all 18 first cases complete; held/release/neutral evidence 18/18; stable intended Calc effect 6/6; naive focus-transfer wrong-surface effect 3/3; candidate wrong-surface effect 0/9 candidate cases; candidate mismatch refusals 3/3; candidate observer-unknown refusals 3/3; naive observer-unavailable actions 3/3 explicitly reported as unsupported by fresh observation; independent audit errors=[]; >=10 copied-evidence corruptions rejected. Any candidate wrong-surface task input/effect is FAIL. Missing process/effect/scorer evidence is STOP/HOLD.

## C
UNO is privileged scorer-only application state, not controller authority. The Tk helper is an explicit wrong-surface fixture. The naive comparator is deliberately weak. Refusal under unavailable observation can reduce liveness even when the stale command happens still to be correct.

## U
One Calc version/X11 container and one single-cell action. No Inkscape transfer, model/planner comparison, screenshot reduction, token/latency benefit, natural focus-change frequency, physical HID telemetry, cross-platform reliability or product promotion.
