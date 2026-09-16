# Inkscape target-centered zoom capability boundary v1

Decision: **PASS_CENTER_SEMANTIC_CAPABILITY_BOUNDARY_SCOPED**.

## Formal A2 result

18/18 fresh first outcomes complete under the frozen held-out layouts x=140/320/460. Frozen audit errors 0. A1 remains separately retained as infrastructure-stopped (2 complete + 2 partial/no-result) and is not pooled.

- `ctrl_wheel`: full scale+center contract **9/9**. Scale ratio median **0.508571**, range **0.456410–0.508571**; x-center residual median **-1.0px**, range **-1.0–2.0px**.
- `native_fixed80`: scale band **9/9**, target-center contract **0/9**. Scale ratio median **0.502857**, range **0.456410–0.508571**; x-center residual median **17.0px**, range **14.0–19.5px**.
- SVG bytes unchanged and terminal contacts/keys/buttons neutral **18/18**.

This is a semantic capability boundary, not a statement that native XI2 pinch is unusable. A single +80px compensation was calibrated only during excluded construction. It preserves scale but does not transfer target-center semantics across held-out positions. The route therefore cannot be silently advertised as equivalent to pointer-centered Ctrl+wheel for `TRANSFORM_VIEW(scale=0.5, center=target_center)` without a current geometry-dependent center lowering or a weaker capability declaration.

## Error check

Independent OpenCV verifier re-reads every pre/post PNG and recomputes red-object bbox, scale and center displacement: **18/18 PASS**. Its first implementation is retained failed only for an incorrect raw touch-trace predicate; formal evidence was unchanged. Lightweight independent semantic integrity checker passes the unmodified 18-row set and rejects seven copied-evidence corruptions **7/7**.

Fresh extraction verifies 276 manifest files and reproduces the unchanged frozen audit plus corrected independent verifier byte-identically.

## Scope

One Inkscape 1.4/X11 fixture, synthetic Xorg DirectTouch, three held-out target x positions. Fixed +80px native compensation is deliberately narrow. No claim about the optimal native center mapping, physical touch, other apps/platforms, model benefit or performance.
