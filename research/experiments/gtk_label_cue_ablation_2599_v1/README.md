# GTK color cue versus text cue — Issue #4862

This is a controlled follow-up to #2599. The earlier local runner paired green TARGET text with green pixels and blue OTHER text with blue pixels. The new runner renders `FIXTURE ITEM` in all conditions, holding GTK geometry/font/foreground constant so only full-window fill color differs.

## Frozen test

16 base X11 captures (8/class), one flattened logistic readout per seed 40–44 (100 full-batch steps), then ten predictions (five seeds × two shifted colors). Xvfb and GTK/model run in separate cached Docker images with `--network=none`; they share only a local read-only X11 client socket. No GPU, model/API provider, online dependency install, retry, or production GUI input.

The authoritative pre-run identities, versions, gates and exact commands are in `FREEZE.json`. `run.py` contains both the no-fit X11 construction check and the one-shot formal path. `audit.py` is a distinct raw-only recomputation/mutation audit. Formal output will be retained under `results/`; this README will be updated only after the one frozen run.

## Scope

This can identify whether the tiny linear probe uses a color cue rather than a class-correlated word. It cannot establish localized target recognition, app transfer, visual robustness, safe runtime authority, GUI success, or human-tempo benefit.

