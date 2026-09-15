# Formal harness repair after retained `-01` failure

The first source-frozen formal attempt (`x11-unicode-clipboard-v1-20260916-01`) failed before any input/clipboard mutation. The matrix was invoked with a relative `--out`, and unchanged `run_arm.py` embedded its relative profile path into LibreOffice `-env:UserInstallation=file://...`; Writer never created an X11 window.

The successor intentionally does **not** change execution source. It reuses the exact frozen `run_arm.py` and `run_matrix.py` blobs and changes only the invocation contract: `--out` is an absolute path. A development calibration with those original source blobs and an absolute matrix output passed both Writer and Calc.

The Unicode corpus, app order, clipboard mechanism, stale/release/keymap/content-restoration gates, scorers, and generic-promotion decision rule are unchanged. The successor uses a new source/plan freeze and result ID.
