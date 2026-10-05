# HUD palette reader repair T1

[Repair and limits](REPORT.md), [ordinary test history](execution-history.json), [retained regression manifest](manifest.json).

Runtime candidate: `research/doom/doom_hud_signal_v4.py`; focused tests: `research/doom/test_doom_hud_signal_v4.py`.

Run ordinary regressions from repository root with Pillow and NumPy available:

```sh
DOOM_TEST_WAD=<hash-bound-freedoom2.wad> python -B -m unittest research/doom/test_doom_hud_signal_v4.py -v
```

The WAD must match SHA256 `a8772e088847032510d97ba2312406a6998f21cbab44d4ff10696faa9c0ecd4b`; the existing default is `_vizdoom/vizdoom/freedoom2.wad`. No package or container installation is performed. The archived inputs remain in the paths bound by `manifest.json`; the original failure controls are #7577's saved031/035 PNGs. This is ordinary repair work; original formal live runs and #7975's first diagnostic must not be repeated to validate it.
