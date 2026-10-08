# Camera-compensated motion screen A01

**Disposition: FAIL_SCOPED.** A fixed global-translation registration did not make adjacent-frame image residuals useful for distinguishing health-loss observations in the retained V39 episode.

## H / T / D / C / U

- **H:** A global translation estimated from grayscale frames and removed before measuring RGB residual will separate health-loss pairs better than raw frame difference.
- **T:** Use every adjacent pair from retained sequences 166–218 (52 pairs). Crop the game world to [321,180,961,584]; downsample grayscale 4×; exhaustively search translations within ±8 downsample pixels (±32 source pixels) by zero-mean normalized cross-correlation; score the overlap with mean absolute RGB residual. Compare against the same crop's unregistered RGB MAE and full-screen RGB MAE. No threshold is fit.
- **D:** Pass only if the compensated feature has AUC ≥0.75, improves raw-world AUC by ≥0.10, and at least 3 of 4 health-loss pairs score above the no-loss median. Otherwise fail the scoped hypothesis.
- **C:** One posthoc episode, with four health-loss transitions. Health deltas are objective typed signals, but are not semantic enemy/attack labels. Translation-only registration may not handle rotation, perspective change, animated surfaces, or occlusion. Four of 52 optimal shifts hit the search boundary.
- **U:** No enemy/attack/player-fire label accuracy, false-interrupt rate, live cue latency, input release, replan quality, task effect, or causal benefit was evaluated.

## Result

| Measure | Value |
|---|---:|
| Adjacent pairs | 52 |
| Health-loss pairs | 4 |
| Full-screen raw-difference AUC | 0.417 |
| World-crop raw-difference AUC | 0.417 |
| Translation-compensated residual AUC | 0.406 |
| AUC gain over raw world crop | −0.010 |
| Loss pairs above no-loss residual median | 1/4 |
| Exact permutation p, raw world / compensated | 0.607 / 0.562 |
| Median world residual, raw / compensated | 16.829 / 15.021 |

The preregistered criterion failed. Registration reduced typical pixel difference, but did not improve health-loss ranking. The result rejects this fixed translation-only feature for this screen; it does not reject more capable motion estimation or object-level visual cues.

The independent auditor recomputed all 52 rows and checked the pinned retention-manifest and event-log hashes, all 53 PNG hashes, typed RGB hashes, sequence-to-image joins, health labels, capture intervals, registration shifts, residuals, AUC, and disposition. Audit status: PASS_EVIDENCE_AND_RECOMPUTATION_SCOPED.

## Reproduction

From the repository root, create a unique temporary output directory and run:

    $out = Join-Path $env:TEMP ('issue59-motion-a01-' + [guid]::NewGuid().ToString())
    python -B research/doom/camera_compensated_motion_a01_20261008/probe.py --repo-root . --out $out
    python -B research/doom/camera_compensated_motion_a01_20261008/audit.py --repo-root . --package research/doom/camera_compensated_motion_a01_20261008

The output directory must be new. The run uses the existing V39 PNGs and JSONL; screenshots are not duplicated in this package. FREEZE.json pins GitHub main at 1aaa633c4f1aeec25e4b4617d92dd93af3b20603 and hashes the source manifest and event stream. The dataset files were checked against that commit before execution.

The first script invocation failed before writing a result because the residual helper assumed a two-dimensional array while receiving RGB. The helper was corrected to use the first two dimensions; the frozen experiment then ran once to completion and the independent audit passed. This development failure is disclosed in DEVELOPMENT_FAILURE_01.txt and the invocation history is in RUN.json.

No game, model, GUI, physical input, container, GPU, or live allocation ran.