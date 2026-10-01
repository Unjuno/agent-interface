# #4424 bounded mid-drag visual effect servo — fresh allocation-02 plan

Allocation: `inkscape-effect-servo-4424-20260926-02`
Owned additive path: `research/integration/inkscape_effect_servo_v2/**`
Predecessor allocation-01 is immutable `STOP_EXECUTION_SURFACE_TIMEOUT_CASE5_INCOMPLETE`; its five complete rows are not pooled or reused.

## Changed factor from allocation-01
Scientific source, policies, schedule cells, target, observation point, tolerance and audit logic are byte-identical except allocation metadata. Only **external orchestration granularity** changes: allocation-02 is supervised one formal case per tool/container invocation, rather than a 12-case outer shell that exceeded the execution surface envelope. Each case remains single-use and `execute.py` still requires all preceding fresh allocation-02 cases to be complete before the next index.

## H
With Selector/100%-zoom and the fixed selected red rectangle, a fixed open-loop pointer endpoint can under-travel at the saved object effect. One current screenshot while Button1 remains held can expose the actual rectangle displacement; changing only the remaining endpoint once by the observed residual can reach the requested saved effect without a new planner/model boundary. Missing observation must release/YIELD, not guess.

## T
Provided Linux x86_64 execution container; CPython 3.13.5, Inkscape 1.4, Openbox, authenticated TCP-disabled Xvfb, Python-Xlib/XTEST, Pillow/NumPy. No model/provider, network experiment, user desktop/data, package installation or public-runtime dispatch. Saved SVG is evaluator-only after release.

Formal: first-motion offsets `(5,3)` and `(10,6)` × three policies × two fresh repetitions = 12 sessions in SCHEDULE.json. Shared hold prefix ends at pointer delta `(30,18)`.
- `OPEN_LOOP`: one mid-hold image is retained but control continues to authored pointer delta `(50,30)`.
- `MID_EFFECT_SERVO`: exactly one delivered mid-hold image; measure current red-rectangle displacement, residual=`(50,30)-observed_effect`; exactly one corrected endpoint=`current_pointer+residual`; then release.
- `SERVO_OBSERVER_UNAVAILABLE`: withhold the mid effect image from the controller, release immediately at `(30,18)`, zero corrective motion, YIELD.

No second drag, undo, semantic replan, same-ID retry, replacement, pooling, threshold/source tuning or compensating second correction. Each `execute.py INDEX` is invoked once in a separate outer tool call; stop at first nonzero/incomplete case.

## Variables / units
- X pointer coordinates/deltas: integer screen pixels.
- screenshot effect displacement: integer screen pixels from independently reconstructed red-component bounding-box centers.
- saved effect: SVG user units from `<rect x,y>`; fixed fixture mapping is tested only here, not generalized.
- desired saved delta: `(50,30)` SVG user units.
- mid pointer delta: `(30,18)` screen pixels.
- saved target tolerance: absolute 0.1 SVG user unit per coordinate.
- expected directed OPEN_LOOP saved delta: first `(5,3)` -> `(45,27)`; first `(10,6)` -> `(40,24)`.
- expected mid screen effect: first `(5,3)` -> `(25,15)`; first `(10,6)` -> `(20,12)`.
- expected servo corrected pointer endpoint: `(55,33)` and `(60,36)` respectively.

## D
`PASS_MID_DRAG_EFFECT_SERVO_SCOPED` only if all 12 fresh allocation-02 cases, wrappers, sources and process evidence are complete and:
1. every OPEN_LOOP reaches pointer `(50,30)` and retains the frozen nonzero saved-effect error for its first-step cell;
2. every MID_EFFECT_SERVO has one delivered mid image, observed effect equal to independent image reconstruction, correction_count=1, the frozen corrected endpoint, and final saved delta `(50,30)` within 0.1/coordinate;
3. each matched servo saved absolute error is strictly lower than OPEN_LOOP;
4. observer-unavailable has no delivered mid effect, correction_count=0, decision YIELD, pointer `(30,18)` at release, no completion claim;
5. all cases expose one Button1 press/held/release, final and cleanup input neutral, one unchanged-size rectangle/no transform/collateral; authority none/model_calls0;
6. separate raw-only audit errors=[] and >=10 effective copied-evidence corruptions reject.

Complete candidate wrong/collateral effect => FAIL. No error reduction => FAIL/HOLD according to complete evidence. Any incomplete denominator/source/process/raw evidence => STOP/HOLD. No case is rerun or replaced.

## C
Rendering delay, X event coalescing, drag threshold, selection semantics and this fixture's pixel↔SVG relation can explain behavior. The candidate adds one screenshot and local computation. A red component is a declared fixture feature, not authenticated semantic identity.

## U
One selected red rectangle, one Inkscape/X11 setup, two technical repetitions. No natural failure rate, planner/model usefulness, token or wall-time benefit, physical HID timing, arbitrary document, atomic check/use, public runtime, cross-platform or product claim. Same-author separately structured audit is not independent human review.
