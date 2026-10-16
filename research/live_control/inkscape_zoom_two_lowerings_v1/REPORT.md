# Inkscape real-app ZOOM_TO multi-route lowering v1

Decision: **PASS_INKSCAPE_ZOOM_MULTI_ROUTE_SCOPED** under the frozen **scale-only** visible-effect contract.

## Formal result

Twelve fresh first outcomes completed, four per route. Frozen audit: 12/12 pass, errors 0.

- native XI2 two-contact pinch: 4/4 semantic effect; width ratio **0.486405** in every case;
- Ctrl+wheel-down x2 with Control_L: 4/4 semantic effect; width ratio **0.489426** in every case;
- one-contact DirectTouch negative: 4/4 non-equivalent; width ratio **0.975831** in every case;
- SVG bytes unchanged 12/12;
- adapter contacts empty, keymap empty and pointer buttons neutral 12/12.

Frozen semantic instruction was `ZOOM_TO(target=red_rect, scale=0.5)` and the predeclared effect scorer required post/pre visible object width ratio 0.45..0.55 for valid lowerings. The negative route had to remain in 0.85..1.15.

## Independent error check

The independent postformal verifier does not import the measured runner or frozen audit. It re-reads every pre/post PNG with OpenCV, independently reconstructs the largest red-dominant connected component, recomputes the width ratio, checks route provenance/order, semantic instruction, SVG source hash and terminal resource fields. Corrected verifier: **12/12 PASS**. Seven copied-evidence semantic corruptions are rejected **7/7**.

The first postformal verifier implementation is retained failed. It incorrectly searched for `route_trace.kind == "touch"` even though the raw trace correctly stores `begin/update/end`; this false-rejected the four native cases. Measurement evidence was unchanged; only the postformal verifier condition was repaired.

## Important posthoc route difference

The two valid lowerings are **not proven equivalent as full target-centered transforms**. The preregistered gate scored scale only. Posthoc, the visible target bbox center moves by median **-41.0 px in x** for native XI2 pinch but only **+1.5 px** for Ctrl+wheel; y displacement is 0.0 versus +0.5 px. This difference is perfectly repeated across the four cases in each route.

Therefore the retained claim is narrow: both routes realize the same requested visible **scale** effect and release resources correctly. The result does not justify hiding center/translation semantics in a route-polymorphic `ZOOM_TO`. A successor should freeze a 2D similarity-transform contract including center displacement before comparing or calibrating routes.

## Scope

Inkscape 1.4, X11/XInput2, Xorg `inputtest` synthetic DirectTouch and ordinary XTEST key/wheel events. One simple SVG, no model call, no task productivity or latency claim, no physical-touch/HID fidelity and no cross-platform claim.
