# Patch anchor feasibility — 2026-09-13

Following the actual assistant's 13.39-second reply miss, this pilot explores a
deterministic effect sensor for planner-declared bounded local correction.
It is an offline component, not an integrated servo or runtime promotion.

Image-patch search is described in the official
[OpenCV tutorial](https://docs.opencv.org/4.12.0/de/da9/tutorial_template_matching.html).
This candidate uses NumPy mean absolute RGB error, not OpenCV's correlation methods.
OpenCV was absent from WSL Python; no dependency was installed.

`visual_anchor.py` copies a planner-specified rectangular source patch, rejects
spatially flat patches and searches within a bounded radius of its original
location. A second candidate outside the tolerance neighborhood must have enough
error margin. `lost` and `ambiguous` results omit coordinates. Error/margin are not
calibrated probabilities. Changed frame labels/dimensions and same-source observation
are rejected. Caller-supplied identity labels are not freshness proof. This sensor
grants no input authority and must not replace owner/lease guards.

## Evidence

Frozen runner seed 991006 uses radius 32 px, maximum normalized error 0.03, minimum
margin 0.005 and neighborhood tolerance 2 px. Four generated fixtures pass: exact
displacements (19,0) and (-21,17), ambiguous duplicate, and lost target. Three more
checks reject wrong frame, same observation and flat source.

Historical Inkscape cohort 03 replay uses patch [592,369,56,44], including object
boundary and background. Frames 2 and 3 return (0,0) and (23,0), consistent with
saved-object evidence. Unlike the earlier detector, no target color is encoded.
The images were already known; this is not fresh-case validation. Thresholds were
not tuned after this run. Source/input hashes, NumPy version and raw results are
recorded in `results/visual-anchor-01`.

Single-call times: 25.3–31.0 ms on generated fixtures and 58.9/65.3 ms on replay.
These exclude capture, inference, tool transport and input. They do not establish
a latency distribution, model performance or end-to-end speedup.

## Remaining integration gate

Search stays relative to the original patch, without scale/rotation adaptation or
template updates. Similar objects outside that region are not considered. Occlusion,
selection decorations, changing background and repeated structures remain failure
modes. A unique local match does not prove object identity. Public Python attributes
are not a security boundary.

Next connect planner-declared targets and bounded corrections to existing yield and
owner checks, with explicit lost/ambiguous termination. Test fresh positions and
distractors in actual apps with independent endpoint/collateral scoring. Synthetic
checks and historical replay do not satisfy that gate. Preserve remote correction
as a separate baseline; no promotion, freeze credit or human-speed claim.
