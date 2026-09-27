# #4424 bounded mid-drag effect servo — first complete formal result

Allocation: `inkscape-effect-servo-4424-20260926-02`  
Disposition: **PASS_MID_DRAG_EFFECT_SERVO_SCOPED**

## Chronology

Allocation-01 remains immutable `STOP_EXECUTION_SURFACE_TIMEOUT_CASE5_INCOMPLETE`: cases0–4 complete, case5 incomplete, cases6–11 unstarted. No row is pooled or reused. Allocation-02 changed only outer supervision granularity and executed 12 fresh cases, one separate outer invocation each, fixed order, reruns/replacements/tuning 0.

## Result

| policy | cases | final pointer delta | saved object delta | correction | disposition |
|---|---:|---|---|---|---|
| OPEN_LOOP first(5,3) | 2 | (50,30) | (45,27) | 0 | open-loop completion |
| OPEN_LOOP first(10,6) | 2 | (50,30) | (40,24) | 0 | open-loop completion |
| MID_EFFECT_SERVO first(5,3) | 2 | (55,33) | **(50,30)** | exactly 1 | corrected once |
| MID_EFFECT_SERVO first(10,6) | 2 | (60,36) | **(50,30)** | exactly 1 | corrected once |
| OBSERVER_UNAVAILABLE first(5,3) | 2 | (30,18) | (25,15) | 0 | YIELD |
| OBSERVER_UNAVAILABLE first(10,6) | 2 | (30,18) | (20,12) | 0 | YIELD |

Both servo cells used one screenshot while Button1 remained held. The independently reconstructed mid-screen effects were (25,15) and (20,12), respectively. The controller computed residuals (25,15) and (30,18) and changed only the remaining endpoint once. All four servo cases saved exactly the target (50,30) within the frozen 0.1 SVG-unit tolerance; matched open-loop errors were (5,3) and (10,6). Observation-unavailable cases released immediately without a corrective motion or completion claim.

## Integrity

- formal cases: 12/12
- worker exits: 12/12 zero
- outer supervision exits: 12/12 zero
- held Button1 observation: 12/12
- final + cleanup input neutral: 12/12
- Inkscape teardown: expected SIGTERM -15 in 12/12; Openbox/Xvfb exit0 in 12/12
- frozen raw-only audit: 117 checks, `errors=[]`
- copied-evidence controls: 11/12 rejected. The single non-rejection mutates only the derived `saved_effect_error` convenience field, which the frozen raw auditor deliberately recomputes/does not consume. The prospective gate requires >=10 effective rejections; 11 independent mutations are rejected. The original controls exit1 is retained rather than rewritten.
- all nine SHA-bound source/plan/environment dependencies unchanged after formal.

## Interpretation

This scoped fixture shows that one current application-effect observation can change a later action inside the same bounded hold and eliminate the directed endpoint error without a second planner/model boundary. It does not establish a general visual servo. The experiment's red component is a declared fixture feature, not authenticated semantic object identity; screen-pixel displacement and SVG units are separate quantities even though this fixed 100% fixture supports the tested correction.

## Limits

No public Agent Interface runtime/CLI/MCP dispatch, model/provider, task-token or wall-time benefit, natural failure rate, arbitrary Inkscape document, physical HID timing, atomic check/use, cross-platform or product claim. Same-author separate raw audit is not independent human review.
