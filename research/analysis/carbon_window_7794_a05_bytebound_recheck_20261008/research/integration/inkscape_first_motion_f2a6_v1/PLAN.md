# Inkscape first held-motion boundary — #4388

Allocation: inkscape-first-motion-f2a6-20260926-01.
Base: 4c701cc51b06296268ad8d9ae3eff1dd6f2d379d.
Only additive research/integration/inkscape_first_motion_f2a6_v1/**.

## H
At fixed Selector/100% zoom, object displacement depends on the first held
motion even when start/end pointer coordinates and all later path points agree.
The stronger endpoint-minus-first-offset model is checked separately, not used
to force the primary decision. Excluded construction already contradicts that
model for first(2,1), saved delta(35,21); first(8,4) gave delta(42,26). Preserve
this as evidence against a universal first-event model. No source-level cause
or production bug is established. No compensation is implemented.

## T / fixed allocation
8 fresh authenticated, TCP-disabled private Xvfb/Openbox/Inkscape sessions.
First offsets in screen pixels: (1,0),(5,3),(10,6),(-5,-3), then reverse order.
The second half is a new repetition, not re-execution of prior case IDs.
Common later offsets: (15,9),(20,12),(25,15),(30,18),(35,21),(40,24),(45,27),(50,30).
Nine task motions, one Button1 press/release, no corrective drag per session.
Fixed motion pause35ms, button pause45ms. ROI screenshots after each motion add
observation work equally in all cases. These are not timing-performance trials.
Two earlier construction cases with different first points are excluded.

Original SVG rectangle: x50,y50,width40,height30, viewBox0 0 200 200,
200x200 document. Fixture setup invokes F1,1,Ctrl+A once after mapped-window
activation and a900ms settle; readiness then requires one red component with
38..42 by28..32 threshold extent. No task-input retry on missing readiness.
Capture source screenshot plus160-ish by130-ish local image region per motion.
Save via separately labelled Ctrl+S after task, then score the full saved SVG.
SVG reads are evaluator-only and never drive the task path.

Before formal: publish readable scientific source, schedule, environment,
construction audit/control receipts, this plan and hash manifest; verify exact
Git blob identity/readback. Construction raw and audit-v0 source are retained
locally and delivered with the complete post-allocation evidence.
Formal command, each index once, sequential0 through7:
`python -B execute.py formal INDEX`
Wrapper worker limit25s; cleanup escalation8s then2s. Caller records actual
wrapper exit separately. Every prior index must have an observed successful
worker exit before a later index is eligible. First incomplete case stops the
allocation; no replacement, tuning, resumption or pooling. Audit only afterwards:
`python -B audit.py . formal` and `python -B test_audit.py . formal`.

## D
Primary PASS_FIRST_MOTION_DEPENDENCE_SCOPED requires8 complete source/process
bound cases, exact pointer endpoint(50,30), neutral/release evidence, original
single rectangle/size preservation, saved-SVG/rendered displacement agreement
within1 screen pixel, and at least two distinct saved displacements in EACH
repetition. No variation => HOLD_NO_FIRST_MOTION_DISCRIMINATOR.
Incomplete/source/raw/process/control evidence => HOLD_INCOMPLETE_OR_INTEGRITY.
All eight effective corruption controls must reject from an error-free baseline.
Simple-model match requires each coordinate within0.25 SVG user units of final
pointer offset minus FIRST offset. Report count and reject universal model when
any complete case contradicts it. This separate rejection does not erase primary
dependence. Natural rates, model usefulness and speed are not decision gates.

## Variables and dimensional check
| Symbol | Japanese meaning | Unit (SI status) | Definition | Domain/assumption | Type |
|---|---|---|---|---|---|
| p0 | 押下前のpointer位置 | screen pixel, non-SI | queried root x,y | private display integers | 2-vector |
| f | 最初の保持中移動offset | screen pixel, non-SI | one frozen first pair | four declared pairs | 2-vector |
| e | 最終pointer offset | screen pixel, non-SI | (50,30) relative to p0 | same all cases | 2-vector |
| d | 保存図形変位 | SVG user unit, non-SI | saved rect minus original rect | evaluator only | 2-vector |
| s | 画面と文書の倍率 | pixel per SVG unit, non-SI ratio | nominal1 at100% | raster extent tolerance1pixel | scalar |
| eps | 図形予測の許容差 | SVG user unit, non-SI | 0.25 per coordinate | fixed diagnostic tolerance | scalar |
| k | uncertainty coverage factor | dimensionless | not assigned | no calibrated uncertainty model | unavailable |

The model in words is d=(e-f)/s. Pixel differences divided by pixel per SVG unit
have SVG-unit dimension. Pixel and document coordinates are never presumed to
be SI metres or universally interchangeable. At first(5,3), model predicts
(45,27); that is a hypothesis, not a guaranteed GUI effect.

## C / U
Same supplied Linux container, private narrow red shape, fixed mode and zoom,
quiescent focus, one XTEST producer, same pacing and screenshot work. No full
public runtime admission/lease/CLI is exercised. X-server state is not physical
HID state; sync returns do not reveal exact application-event coalescing.
Small motions can fail to initiate dragging; threshold and event handling are
not separately manipulated, so unique source-level attribution remains unknown.
Image threshold support can be39x29 for a40x30 object; preformal audit_v0's exact
extent error and its corrected1-pixel extent tolerance are retained unchanged
in construction_history. GUI construction was not rerun for this audit repair.
Actual environment/binary/package hashes are in ENVIRONMENT.json. Docker and
Podman absent; no image-attested replication, installation or network experiment.
No model/provider/user-desktop/user-document trials, task-efficiency or token
savings, arbitrary-document transfer, hard deadline or product claim. Two
technical repetitions give finite coverage only; no combined calibrated u_c or
coverage factor k is fabricated. Same-author separate auditor is not external
human review.

## Preservation / roadmap
Old m7c4 remains HOLD10/12. Original ZIP SHA256
 e01decd31651aaab9ea9514ad62976f9d6e7b638a4fe456a3f061577369382c4
was restored371 members,395 read-only checks; old GUI reruns0. It is not included
in this new study's case count or complete evidence archive. Full old ZIP is a conversation
attachment, not claimed remotely complete here.
Construction -> public freeze ->8 cases ->independent raw reconstruction/controls
-> complete additive evidence PR ->applicable exact-head checks and scoped review
-> qualified evidence-only merge/readback. No foreign branch cleanup. Global
ROADMAP remains open; this tests an endpoint-calibration assumption, not a repair.

Official background: Inkscape keyboard/mouse reference, https://inkscape.org/sl/doc/keys.html
(F1 Selector and mouse dragging). Installed1.4 selector source was not retrieved;
no source-code diagnosis is inferred from a different online revision.
