# Camera block-motion screen R02 conditions

- Frozen main: `893c3400c694586ff42d30e2f8fa42f5868f5bba`.
- Freeze/code commit before execution: `5e005a873af04daed3abf0ff945cc2b259cc1c1a` (contains `FREEZE.json`, `probe.py`, and `audit.py`).
- Dataset: existing current-main V39 episode `research/doom/results/map01-v39-coast-liveness-live-01`; extracted read-only from frozen main. Retention-manifest SHA-256: `8dfbac52c298d865b4484aaa51dc0d821bb0d74f8c5995d3117206a1ed0dbda2`; event-log SHA-256: `2c917658e8bba0a94e5a34f0ee3d968553cd56950105196871012f2e3eedb381`.
- Local data root used: `D:\CodexData\Temp\agent-interface-camera-block-motion-r02-data-ab9593ec81444f0ba4b125e0db811704` (dataset-only archive extraction; no source files modified).
- Host: Windows CPython 3.11.9, NumPy 2.4.6, Pillow 10.2.0. OpenCV, SciPy, and scikit-image were absent and not installed or used.
- Candidate: one normal run and one `-O` run of `probe.py`, each over all 52 adjacent pairs. Both commands and exit codes are retained in `raw/`.
- Method: crop `[321,180,961,584]`; 4x grayscale block-mean downsample; exhaustive normalized cross-correlation for each fixed 16x16 downsampled tile, search radius ±8 samples; exclude the outer tile row/column and average 32 full-resolution 64x64 RGB residuals. Tie-break and scoring are frozen in `FREEZE.json` and code commit.
- Comparator and labels: same episode, same objective typed health-loss labels, raw world-crop RGB MAE, and the R01 global-translation method. There are only four positive pairs; this is repeated analysis of the same episode, not independent confirmation.
- Decision rule inherited unchanged from R01: AUC at least 0.75, gain over raw AUC at least 0.10, and at least 3/4 loss pairs above the no-loss residual median. No threshold fitting, pair selection, or post-result tuning.
- Independent audit: `audit.py` recomputed source provenance, all 53 PNG/RGB hashes, all 52 labels, raw/global/blockwise metrics, 1,664 local tile offsets/residuals, the R01 anchor, and the frozen criterion; normal and optimized audit outputs are retained.
- No game, model/provider, GUI, physical input, container, GPU, package installation, or live allocation ran.
