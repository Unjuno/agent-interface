# Pixel-identical target replacement versus footprint identity — retained result

Task `FOOTPRINT-IDENTICAL-REPLACEMENT-20260916-001`, Issue #347. Publication BASE `4e802fa2ec3c0c97545a38520bb18b3b126d8e4e`; source-first freeze HEAD `d6074ccca64dd578d71502bda91e07d712edf201`.

## Decision

**`RETAIN_IDENTICAL_REPLACEMENT_BOUNDARY`.**

The current fixed-scale footprint resolver can reacquire appearance, but it cannot establish semantic object incarnation when the replacement is pixel-identical. This is a scoped observability boundary, not an OpenCV defect and not a regression in the earlier #335 fixed-scale/decoy result.

## Frozen experiment

The exact current-main resolver snapshot is retained as `upstream_resolver.py` and matches Git blob `a8bb0e564bae738c9091b737ff2abe1922520ec1`. Eight matched pairs / sixteen first current arms were rendered independently with unmodified Inkscape 1.4 at 600x400. Each reference contains SVG object `target-A` at `[175,155]`. Both current arms receive the same frozen translation and identical geometry/style:

- `stable`: the moved object remains `target-A`;
- `replacement`: `target-A` is absent and an otherwise identical `replacement-X` occupies the same current geometry.

The resolver sees only reference/current RGB evidence and the source prediction. XML IDs are evaluator-only. No pointer/keyboard/task input, model call, game call or shared-runtime mutation occurs.

## First outcome

All hard gates pass.

| pair | translation px | resolved point px | best RMSE | second RMSE | stable↔replacement pixels | replacement original ID |
|---:|---:|---:|---:|---:|---|---|
| 0 | `[47,23]` | `[222,178]` | 0.0000 | 91.0684 | exact | absent |
| 1 | `[-53,41]` | `[122,196]` | 0.0927 | 79.4234 | exact | absent |
| 2 | `[69,-34]` | `[244,121]` | 0.0974 | 77.6866 | exact | absent |
| 3 | `[-71,-29]` | `[104,126]` | 0.0803 | 86.4146 | exact | absent |
| 4 | `[18,76]` | `[193,231]` | 0.0000 | 71.9922 | exact | absent |
| 5 | `[84,7]` | `[259,162]` | 0.1096 | 73.4146 | exact | absent |
| 6 | `[-33,68]` | `[142,223]` | 0.0000 | 72.8439 | exact | absent |
| 7 | `[61,55]` | `[236,210]` | 0.0552 | 86.7343 | exact | absent |

For every pair:

- stable and replacement current PNG bytes and decoded RGB arrays are identical;
- stable resolves `UNIQUE`, eligible, at the exact translated point;
- replacement returns the same decision-relevant resolver evidence byte-for-value despite `target-A` being absent and `replacement-X` being present;
- independent audit re-runs the matching arithmetic without importing the runner/resolver implementation and passes all 16 rows;
- four offline corruption controls are rejected: semantic-ID receipt, resolver status, resolver point and image pixel.

The observed stable best-RMSE range is `0.0..0.10956250085116624`, far below the frozen `20.0` acceptance threshold; second-match RMSE is `71.99215122398557..91.06841712519656`. Thus this is not a marginal-threshold effect.

## Interpretation

Let the resolver decision be a deterministic function `R(I,T,P)` of current pixels `I`, reference template `T` and prediction `P`. In each matched pair the replacement arm preserves all three inputs exactly: `I_replacement = I_stable`, `T_replacement = T_stable`, `P_replacement = P_stable`. Therefore `R` cannot distinguish the object-incarnation change. The independent SVG oracle supplies information deliberately unavailable to `R` and proves the task-relevant identity changed.

This is the expected limit of an appearance-only observation channel. A stronger appearance descriptor cannot solve a deliberately pixel-identical incarnation change without some additional evidence source such as temporal provenance, a public semantic/accessibility identity, or effect-owner/application identity. Which additional source is useful is a separate experiment.

## Integrity and retained failure chronology

The formal runner completed all 16 rows and the frozen independent audit completed successfully. The outer combined shell command then hit its timeout while running *offline* corruption tests. The formal allocation was not rerun. The corruption tests were resumed separately using only the already-retained formal bytes and passed 4/4 rejection controls.

Full evidence archive: `target_footprint_identical_replacement_v1_evidence.tar.xz`, 104,500 bytes, SHA-256 `80aee92a6970b5efe0b1ef91c35a2b37e05f7e5b1227c1ed17514cbf29793773`; 95 files; canonical manifest SHA-256 `d7249d13f54f1aac0a3c4390205abad2b2d38cf6ac427d7a4f616bd807721756`. Archive extraction was re-hashed member-by-member.

## Environment / limits

Linux 6.18.44, CPython 3.13.5, Inkscape 1.4, OpenCV 4.13.0, NumPy 2.3.5, Pillow 12.3.0, Intel Xeon Platinum 8370C guest, visible CPUs 0..4, batch 1. CPU frequency/host contention are unpinned. Renderer elapsed values (32 renders) are retained only as diagnostics: median 691.160 ms, min 632.419 ms, max 758.246 ms; **no performance claim** follows.

The identity relevance here is task-authored through SVG IDs. This does not claim every visually identical replacement matters semantically, estimate a natural replacement rate, test occlusion/history, prove accessibility availability, or establish a general cross-application identity mechanism. It establishes only that the current appearance-only footprint evidence is insufficient when semantic identity changes without a pixel change.

## Next one-variable question

Do not add a larger tracker immediately. The next discriminating rung should add exactly one *non-pixel identity evidence source* and test whether it distinguishes the same stable/replacement pair while preserving the fixed appearance evidence. Existing active AT-SPI work (#339) already owns one such Inkscape semantic-source lane, so this allocation does not duplicate it.
