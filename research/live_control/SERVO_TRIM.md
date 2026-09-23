# Separate acquisition from appearance-tolerant tracking — 2026-09-13

Candidate session_v20 / patch_servo_v4 uses untrimmed source uniqueness screening
from visual_anchor_v2, then tracks with visual_anchor_v3. Tracking drops the largest
10% of per-pixel RGB-mean residuals before averaging. Source image and template are
unchanged; there is no online template learning or new input authority. This is an
appearance-tolerance experiment, not temporal object-identity resolution.

## Diagnostic evidence

`probe_patch_residuals.py` evaluates three known image pairs with 0/10/20% trimming.
In the red-distractor failure, the intended object error is 0.04858 while the
neighbor scores 0.01398: raw matching actually prefers the wrong object. Trimming
10% makes those 0.01043 and 0, so trimming alone does not solve identity. At 20%,
both score zero and location discrimination deteriorates.

For the blue-distractor image after a successful 12 px physical move, the correct
location already ranks first but error 0.05774 exceeds 0.03. Ten-percent trimming
reduces it to 0.01721. This supports testing appearance tolerance separately from
acquisition ambiguity. The diagnostic's radius-8 windows are centered on annotated
reference positions: that is oracle-assisted diagnosis, not an online tracking
method or controller evaluation. No controller consumes those annotations.

## Actual-app attempts, all retained

| Cohort | Candidate | Blue distractor | Red distractor |
|---|---|---|---|
| 04 | session19: trimmed acquisition and tracking | rejected, 0 px | rejected, 0 px |
| 05 | session20: raw acquisition, trimmed tracking | completed, +12 px | rejected, 0 px |
| 06 | frozen session20, shifted fixture | completed, +12 px | rejected, 0 px |

Cohort 04 over-rejects the blue case: trimming also makes displaced source matches
too plausible. It is not promoted. Cohort 05 separates the two error policies and
meets the ±1 px goal with target y/size/transform and distractor geometry preserved.
Cohort 06 changes target SVG position from (50,50) to (55,60), distractor from
(74,50) to (79,60), retaining the same size/color/relative spacing and thresholds.
Both outcomes repeat. This is one new absolute position, not broad held-out coverage.

All decisions are scripted; source acquisition uses the fixture ROI selector,
not a model. Control uses screenshots and shared pointer authority; XML is only
setup/final independent scoring. Red-case rejection is prevention, not task success
or recovery. A planner still needs a different route to complete that task.

`audit_servo_trim.py` verifies 36 exact frames, listed source hashes, saved attributes,
recorded release verification, blue precision and no servo admission/input for red
rejections. Probe processes exited normally; child cleanup has no separate attestation.
The diagnostic manifest lists script and image bytes, not every metadata dependency.

## Remaining risks and decision

Dropping residuals can hide meaningful small changes or occlusion. The source gate
does not protect against a new distractor appearing later. No continuous target
identity, dynamic target disappearance, scale/rotation or cross-domain robustness
has been demonstrated. Original local latency/CPU costs and the double preflight
search need separate matched profiling; no speedup or token claim is made.

Keep session20 as a candidate only; existing CLI evidence stays frozen. Next test
negative partial-occlusion/target-loss cases and planner recovery, preserving the
original wrong-anchor trajectory. This result does not justify broader motor
primitives or benchmark promotion before those correctness gaps are addressed.
