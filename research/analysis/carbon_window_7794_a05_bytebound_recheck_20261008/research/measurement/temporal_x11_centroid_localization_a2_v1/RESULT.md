# X11 centroid localization A2 first outcome

Issue: #1326  
Task: `TEMPORAL-X11-CENTROID-LOCALIZATION-A2-20260918-009`  
Frozen scientific decision: **HOLD_X11_LOCALIZATION_BOUND_WIDER**

The sole A2 harness repair (runner-side `DISPLAY`/`XAUTHORITY`) reached the unchanged #1312 science path. One construction session and one formal supervisor invocation completed; formal reruns/replacements/tuning were zero.

## Formal result

- 4/4 private sessions cleaned up; fixture exit0, Xvfb exit0, sockets removed.
- 800/800 frames and400/400 pairs complete.
- missed red detections:0.
- direction agreement:400/400.
- max absolute point error: **0.990 px**.
- p99 absolute point error: **0.980 px**.
- max absolute displacement residual: **0.700 px**.
- median raw XGetImage one-scanline acquisition: **35.603 µs** (descriptive only).

The preregistered point gates were <=0.75 px for max and p99, so this allocation is a HOLD. The displacement residual and direction gates pass. Signed point error spans -0.99..0.00 px: this easy Tk/Xvfb rectangle is rasterized onto integer pixels with a one-sided phase-dependent centroid quantization. Signed displacement residual takes only {-0.7,-0.3,+0.3,+0.7} px in the retained allocation.

## Integrity caveat retained

The frozen `corruption.py` reports4/4 rejected, but its scheduled scanline mutation changes an arbitrary leading base64 byte. On the already-HOLD first outcome the frozen auditor returns `errors=[]` and only the pre-existing point-error science gates, so that specific corruption control is **non-discriminating**. This is retained as an audit-tooling defect rather than hidden.

A separately labelled read-only diagnosis changes an actual retained red pixel and the frozen auditor detects `scanline_recompute` (plus derived point/residual mismatches). Source rehash is exact5/5. No scientific rows were regenerated and the frozen HOLD is not relabelled.

## Scope

This measures only a saturated12x24 red rectangle on black in private Xvfb/Tk with a known scanline and trivial color centroid. It is not a semantic visual-localization bound and does not validate compositor/scaling/occlusion or a temporal controller. The direct next transfer should use the **measured 1.0px-safe point envelope (not the rejected0.75px gate)** as a preregistered bound in a fresh X11 reversal sequence, keeping cadence and estimator fixed.
