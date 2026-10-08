# Inkscape XI2 native pinch transfer v1

Decision: **PASS_INKSCAPE_XI2_PINCH_TRANSFER_SCOPED**.

A1 stopped on outer orchestration timeout after one complete first outcome and one partial/no-result directory; A1 was not resumed or pooled. A2 changed orchestration only and completed 12/12 fresh first outcomes with the unchanged scientific source and thresholds.

## Results

- two-contact native XI2 pinch: 4/4 PASS; width ratio median **0.407855**, range 0.407855–0.407855;
- one-contact move: 4/4 negative control PASS; median **0.993846**, range 0.975831–0.993846;
- no-input matched wait: 4/4 negative control PASS; median **0.981873**, range 0.981873–1.000000;
- SVG bytes unchanged 12/12; adapter active logical contacts empty 12/12; Button1 neutral 12/12.

The visible scale change is specific to the two-contact stream in this fixture and is not reproduced by a single touch contact or idle rendering drift. The SVG document bytes remain unchanged, so the scored effect is a viewport/view transform rather than document mutation.

## Error check

Frozen independent audit: 12 cases, 12 pass, errors 0. Independent postformal verifier: **PASS**. SHA-bound retained-evidence corruption controls: **6/6 rejected**.

## Scope

Inkscape 1.4 / X11 / XInput2 / Xorg `inputtest` synthetic DirectTouch only. This does not establish kernel HID/physical touch fidelity, arbitrary-application gesture behavior, cross-platform semantics, latency/model benefit or task productivity. No independent server API was used to query active touch contacts after termination; terminal touch neutrality is adapter-logical plus completed TouchEnd trace, while Button1 is independently queried.
