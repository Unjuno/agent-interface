# Issue #4561 plan — in progress

The frozen study asks whether broad synthetic template exposure improves a small local grounder's exact paired field/submit coordinate accuracy on unseen whole-template families, compared with a narrow arm at matched optimizer-update and sample budgets.

Current status:

1. **Source/collision review:** #4546, #4482, main's strict compiled form-grounding validator, issue #4561, current main, and the reserved branch/path were inspected. This bundle uses an additive v2 path and preserves prior records.
2. **Local construction:** deterministic 12-family raster renderer, 8×10 heatmap model, fixed-matrix pool, strict validator adapter, one-shot runner, independent audit and mutation tests are implemented.
3. **Construction gate:** 9/9 tests passed in the pinned local CUDA Docker image on the RTX 3080 laptop GPU, including pre-frozen raster hashes, bitwise deterministic CUDA forward/input-gradient repetition and all seven audit mutations.
4. **Freeze/source gate:** pending GitHub source commit, complete blob/SHA readback, frozen invocation manifest and source audit.
5. **Formal:** not started. Exactly one 2,400-update local Docker invocation is allowed only after step 4 succeeds.
6. **Integration:** independently audit frozen raw output; write `REPORT.md` with outcomes or retain `FORMAL_FAILURE.md`; update generated analysis index, open PR, pass CI, merge verified result to main and comment on #4561.

The source-family split is fixed before rendering variants. No test fixture outcome constitutes scientific evidence. The formal output is isolated under an issue-specific host bind mount and is never used to change the frozen code, thresholds, seeds or gates.
