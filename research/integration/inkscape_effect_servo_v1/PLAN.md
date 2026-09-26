# #4424 bounded mid-drag visual effect servo — prospective formal plan

Allocation: `inkscape-effect-servo-4424-20260926-01`
Owned path: `research/integration/inkscape_effect_servo_v1/**`

## H
With Selector/100%-zoom and the fixed selected red rectangle, a fixed open-loop pointer endpoint can under-travel at the saved object effect. One current screenshot while Button1 remains held can expose the actual rectangle displacement; changing only the remaining endpoint once from that measured residual can reach the requested saved effect without a new planner/model boundary.

## T
Provided Linux x86_64 execution container; CPython 3.13.5, Inkscape 1.4, Openbox, authenticated TCP-disabled Xvfb, Python-Xlib/XTEST, Pillow/NumPy. No model/provider, network experiment, user desktop/data, package installation or public runtime dispatch. Saved SVG is scorer-only after release.

Formal: 2 first-motion offsets `(5,3)` and `(10,6)` × 3 policies × 2 fresh repetitions = 12 sessions in SCHEDULE.json. Each case runs once, one private display/profile, one Button1 hold. Shared prefix ends at pointer delta `(30,18)`.

Policies:
- OPEN_LOOP: after the one mid-hold image, continue to authored pointer delta `(50,30)`.
- MID_EFFECT_SERVO: use exactly one delivered mid-hold image, measure current red-rectangle displacement from the source image, calculate residual `desired_effect_delta - observed_effect_delta`, and issue exactly one final pointer motion to `current_pointer + residual`, then release.
- SERVO_OBSERVER_UNAVAILABLE: withhold the mid-hold effect image from the controller, release immediately at `(30,18)`, emit zero correction motion and YIELD.

Construction is excluded. Construction-00 (three policies) stopped before science because the parent Python Xlib connection lacked the private XAUTHORITY; construction-01 changed only that setup propagation and completed all three cells at disjoint offset `(8,5)`: OPEN_LOOP saved `(42,25)`, SERVO observed `(22,13)` and corrected once to saved `(50,30)`, unavailable yielded/released at partial saved `(22,13)`.

## Variables / units
- pointer positions/deltas: X-server screen pixels, integer px.
- screenshot target displacement: screen pixels derived from red component bbox centers.
- saved effect: SVG user units parsed from `<rect x,y>`; this fixture is tested, not generalized as a universal pixel↔SVG conversion.
- desired saved effect delta: `(50,30)` SVG user units.
- target tolerance: absolute 0.1 SVG user unit per coordinate.
- open-loop expected effects from retained #4388/#s8n1 lineage: first `(5,3)` -> `(45,27)`; first `(10,6)` -> `(40,24)`.
- expected mid observed screen effects at pointer `(30,18)`: `(25,15)` and `(20,12)` respectively. These are audited as frozen directed controls, not generalized beyond this fixture.

## D
`PASS_MID_DRAG_EFFECT_SERVO_SCOPED` only if all 12 source-bound first cases complete with no retry/replacement/tuning and:
1. every OPEN_LOOP ends at pointer delta `(50,30)` and saves the frozen nonzero effect error: `(45,27)` for first `(5,3)`, `(40,24)` for first `(10,6)`;
2. every MID_EFFECT_SERVO has one mid image, exactly one correction motion, observed effect equal to independent image reconstruction, final saved delta `(50,30)` within 0.1/coordinate, and absolute error strictly lower than its matched OPEN_LOOP;
3. every unavailable case has no delivered mid effect, zero correction motions, decision YIELD, pointer delta `(30,18)` at release and no completion claim;
4. all task cases expose Button1 held, all final/cleanup states are neutral, no extra SVG rectangle/collateral geometry, authority remains none;
5. separate raw-only audit errors=[] and >=10 effective well-formed copied-evidence corruptions reject.

Complete candidate wrong/collateral effect => FAIL. Candidate fails to reduce effect error => FAIL/HOLD according to complete evidence. Any incomplete case/source/process/raw denominator => STOP/HOLD. No case is replaced or rerun.

## C
Rendering latency, X event coalescing, selection/drag threshold and this fixture's coordinate mapping can explain success. The correction has more local work and one extra screenshot; that cost is not zero. A current effect observation does not authenticate semantic object identity beyond the declared red target contract.

## U
One selected red rectangle, one app/backend/display scale, two technical repetitions. No natural failure rate, model/planner usefulness, token or wall-time benefit, physical HID timing, arbitrary document, atomic check/use, public-runtime integration, cross-platform or product claim. Same-author separately structured audit is not independent human review.

## Stop
Exactly 12 scheduled first cases. Stop at first incomplete/nonzero case. No formal rerun, replacement, pooling, post-result threshold/source tuning or compensating second correction.
