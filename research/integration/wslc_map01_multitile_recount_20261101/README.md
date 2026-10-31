# Post-hoc MAP01 multi-tile tracking ablation

The earlier [scene-gate counterexample](../wslc_map01_scene_gate_counterexample_20261101/README.md) preserved an 8x8 center patch while obscuring its surrounding target. This offline ablation asks whether requiring all nine adjacent 8x8 patches in a 24x24 area to have RGB MAD <=32 reduces that particular failure. The candidate accepts only the original point; it does not relocate, consume labels or grant input authority. The initial point comes from the original scorer's oracle-selected first-frame Zombieman center. Target labels are used only to score the resulting point.

| Retained sequence | Fixed: inside / target not labeled / abstained | Wide: inside / target not labeled / abstained | Nine tiles: inside / target not labeled / abstained |
|---|---:|---:|---:|
| aa01, no extra turn | 20 / 0 / 0 | 20 / 0 / 0 | 10 / 0 / 10 |
| aa03, 80 ms turn | 5 / 0 / 15 | 20 / 0 / 0 | 3 / 0 / 17 |
| aa04, attack | 5 / 0 / 15 | 5 / 0 / 15 | 3 / 0 / 17 |
| aa05, turn then attack | 5 / 0 / 15 | 10 / 0 / 10 | 3 / 0 / 17 |
| aa07, 1000 ms turn | 5 / 15 / 0 | 5 / 0 / 15 | 3 / 0 / 17 |
| aa08, 500 ms turn | 5 / 15 / 0 | 5 / 0 / 15 | 3 / 0 / 17 |

Target-not-labeled is an unknown identity outcome, not proof of target disappearance or an unsafe action. The tile rule abstained on those aa07/aa08 frames but also abstained on half the aa01 frames where the initial target was labeled and the old point was inside its reported box. The wide matcher relocates while the fixed and tile methods do not, so this is a functional tradeoff, not an equal-capability contest.

A separate post-hoc synthetic image covers the first target's reported box in magenta except for the original central 24x24 pixels and removes the target label only for synthetic scoring. The nine-tile rule still returns the old point. This shows that even this exact local evidence cannot by itself establish whole-target identity or action safety; the synthetic manipulation is not a live game observation.

`probe.py` pins the six already-merged archive SHA-256 values, checks each frame hash, computes the candidate from pixels and the initial point, applies the retained evaluator labels afterwards, and reconstructs the synthetic image. `result.json` records all per-frame outputs. Run `python probe.py` without optimization, with NumPy and Pillow; it requires the cited sibling archives. Their original independent auditors were also rerun. The candidate, thresholds and datasets were selected after seeing earlier results, all frames within a sequence are correlated, and inputs are ViZDoom game-state images rather than live X11 control frames. No new game/model run, effect, benchmark win, MAP01 completion or general safety claim follows. Issue 57 remains open.
