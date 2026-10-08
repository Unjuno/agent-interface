# Red-component cue cross-episode screen A02

**Result: `FAIL_SCOPED`.** The A01 fixed cue (8-connected red-mask component count below 51.5) fired on 0 of 7 enemy-visible screenshots from the separate V28 fixed-threat episode. Keep this cue out of runtime. This is a positive-only, single-episode holdout, not a detector validation.

## H / T / D / C / U

- **H:** The fixed A01 red-component cue transfers with useful sensitivity to a separate retained threat episode.
- **T:** Apply A01's fixed crop `[321,180,961,584]`, red mask (`R>70`, `R*4>5G`, `R*4>5B`), 8-connected component area range 8–256 px and decision threshold `<51.5` to seven sequence images in `map01-fixed-threat-v28-live-01` (1, 11, 28, 51, 60, 68, 70). No threshold fitting or adjustment. The source event stream joins each sequence to its exact image path; all files are checked against the retained manifest.
- **D:** PASS only if at least 6/7 frames fire; otherwise FAIL_SCOPED and reject cross-episode transfer. Observed: 0/7.
- **C:** This one run uses a different V28 visual path; several images show red overlay-like blocks whose origin is unresolved. Labels here are one worker's visual inspection, without independent adjudication. The seven positives do not estimate false alarms.
- **U:** No negative controls, independent/blind labels, population sensitivity/specificity, live trigger, input release, recovery or task-effect evidence.

## Evidence

| Sequence | Components 8–256 px | Fired? |
|---:|---:|:---:|
| 1 | 120 | no |
| 11 | 121 | no |
| 28 | 128 | no |
| 51 | 82 | no |
| 60 | 81 | no |
| 68 | 84 | no |
| 70 | 63 | no |

The independent row-run/union-find auditor rechecks the raw V28 retention-manifest, event-stream and audit hashes; each PNG's hash and event-to-image join; and all component counts. It passes the evidence integrity and arithmetic check, while the scientific transfer screen fails. The experiment and independent audit were rerun against the retained files in the local checkout, whose source files were verified byte-identical to the pinned current-main commit. Current `main` was `dd9c2cde511a52cf21e80ecbb2eb9edb0dd6f2f8`; the V28 source bytes used here match the current-main files exactly.

This falsifies this fixed rule on these seven held-out threat images. Some V28 frames contain red overlay-like blocks unlike the V39 tuning images; their origin is unresolved, so the cause of the shift is unknown. No threshold was changed after the result. No game, model, GUI, input, GPU, container or allocation ran.

## Reproduction

From the repository root:

```powershell
python -B research/doom/red_component_cross_episode_a02_20261008/probe.py --repo-root .
python -B research/doom/red_component_cross_episode_a02_20261008/audit.py --repo-root .
```

The scripts read the existing retained V28 files on `main`; the seven screenshots are not duplicated in this package. `FREEZE.json` and `SHA256SUMS.json` pin this analysis package and its input hashes.
