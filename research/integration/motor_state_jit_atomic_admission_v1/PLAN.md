# MotorState JIT atomic-admission boundary v1 — #4266

## H
A current-focus check followed by a separate first key can race with a foreign focus transfer. A bounded X11 server-grab section that validates current focus and emits the first XTEST key before releasing the server should preserve the verified Calc recipient in the directed race.

## T
Provided Linux execution container; LibreOffice Calc 25.2.3.2, Xvfb, Openbox, Python-Xlib/XTEST, UNO scorer. Two policies: JIT_THEN_SEND and ORDERED_ADMISSION. Four schedules: STABLE, TRANSFER_BEFORE_CHECK, TRANSFER_AFTER_CHECK_BEFORE_INPUT, OBSERVER_UNAVAILABLE. Two repetitions = 16 fresh Xvfb/Calc/helper lifetimes, four immutable four-case batches. Actual XTEST input only. Server grab is held only across current-focus validation and first task-key publication. Helper focus request is a separate X client. Grab duration is diagnostic, not a performance gate.

Construction is excluded. Formal commands after public freeze:
`python -B batch.py --scenario STABLE --out formal/stable.jsonl`
`python -B batch.py --scenario TRANSFER_BEFORE_CHECK --out formal/precheck.jsonl`
`python -B batch.py --scenario TRANSFER_AFTER_CHECK_BEFORE_INPUT --out formal/race.jsonl`
`python -B batch.py --scenario OBSERVER_UNAVAILABLE --out formal/unknown.jsonl`
Then `python -B audit.py formal/*.jsonl --out AUDIT.json` and `python -B test_audit.py`.

## D
PASS_MOTOR_STATE_JIT_ADMISSION_RACE_SCOPED only if all 16 first cases and process/effect records are complete; stable effects pass in both policies; pre-check transfer refuses in both; weak comparator sends to helper and leaves Calc blank in both directed race repetitions; ORDERED_ADMISSION writes Calc `7` with zero helper text in both directed race repetitions; observer-unavailable refuses; all task-input rows end with relevant keys neutral; authority remains none; raw audit has errors=[] and >=10 coherent evidence corruptions reject. Any candidate wrong-surface effect is FAIL. Missing denominator/process/effect evidence is STOP/HOLD.

## C
XGrabServer serializes X requests at the server boundary and can block unrelated clients; it is deliberately narrow and may be an unacceptable production mechanism. This does not prove global OS atomicity, toolkit-internal recipient semantics, Wayland/Windows/macOS behavior, physical HID routing or hostile-client safety.

## U
Directed finite race only. No natural race frequency, planner/model usefulness, token/screenshot reduction, latency benefit, production admission API or product claim. Grab duration is reported descriptively with no calibrated performance uncertainty.
