# Real distractor pilot: wrong-anchor failure — 2026-09-13

**The existing patch servo is not qualified for multi-object use.** A real Inkscape
case switched its visual match to a neighboring red object and moved the intended
object 48 px left despite a target of 12 px right. Owner/lease bounds remained valid;
they do not establish visual target identity. This falsifies generalization from the
earlier single-object success. Existing CLI candidates remain experimental.

## Fixture and scoring

Two SVG rectangles are created before Inkscape launches: target (50,50,12,10) red,
distractor (74,50,12,10), either blue or red. This is setup only. A scripted planner
selects the leftmost red component in a declared canvas ROI from the source image;
the controller subsequently uses only patch tracking. No XML or engine action API
chooses a correction. Saved XML independently measures target displacement at fixed
118% zoom and preserves y/size/transform plus all distractor geometry attributes.
Color/style and arbitrary document collateral are not comprehensively scored.

The initial launch failed readiness: the existing red target detector excludes runs
narrower than 24 px. `servo-distractor-01` retains the fixture and empty event log;
it timed out before backend creation and has no measured source manifest. Runner v2
uses a declared small-target ROI pixel readiness check only during prepare, then
restores the shared detector. No core readiness or controller threshold was changed.

## Observed cases

| Cohort | Distractor | Target displacement | Result |
|---|---|---|---|
| 02 / session17 | blue | +12 px | needs_decision: tracking lost after correction |
| 02 / session17 | red | -48 px | needs_decision: update limit after wrong-anchor corrections |
| 03 / session18 | blue | 0 px | needs_decision: tracking lost before correction |
| 03 / session18 | red | 0 px | rejected before servo admission/input |

All recorded terminals verify release; distractor geometry and target y/size remain
unchanged. The negative target displacement is still a task failure even though
those collateral checks pass. In the red failure, the first match reports +28 px
at the distractor. Three -16 px corrections follow while the held target moves left.
The final stop occurs only at the declared correction limit. Confidence/margin alone
did not detect this identity switch.

## Narrow corrective candidate

`visual_anchor_v2` exposes the best alternative error and permits explicit source
analysis without manufacturing a new observation. `patch_servo_v2` checks the source
image before movement: any alternative outside the tolerance neighborhood with
error at or below the existing 0.03 match threshold rejects acquisition. Session18
uses this policy during validation and execution. This is more conservative than
the original minimum-margin test. The red fixture is rejected before acceptance;
saved positions remain unchanged.

This gate is **not** a general identity tracker. A later appearing distractor,
occlusion or changing appearance can still break association. Rejection can also
increase planner work. The blue case remains unstable between runs, and the changed
preflight adds timing/work; no causal claim about that difference is established.
No threshold tuning was performed to force that case through. The added source
search runs twice, so overhead and tradeoffs still need measurement.

`audit_servo_distractor.py` verifies 30 exact frames, listed source hashes, saved
attributes, terminal releases and no servo acceptance/admission in the rejected
red case. These are known-case regressions, not held-out proof. The probe processes
exited normally; per-child cleanup attestation remains absent. Source manifests are
listed components, not exhaustive environment manifests.

Next investigate temporal correspondence, decoration sensitivity and planner
recovery rather than treating a stricter stop gate as task completion. Before any
promotion, require fresh multi-object cases and comparison of success/recovery cost.
Do not add more motor primitives on the assumption that current patch identity is
solved. No freeze qualification or human-speed claim.
