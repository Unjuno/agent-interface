# GTK color cue versus text cue — Issue #4862

This is a controlled follow-up to #2599. The earlier local runner paired green TARGET text with green pixels and blue OTHER text with blue pixels. The new runner renders `FIXTURE ITEM` in all conditions, holding GTK geometry/font/foreground constant so only full-window fill color differs.

## Frozen test

16 base X11 captures (8/class), one flattened logistic readout per seed 40–44 (100 full-batch steps), then ten predictions (five seeds × two shifted colors). Xvfb and GTK/model run in separate cached Docker images with `--network=none`; they share only a local read-only X11 client socket. No GPU, model/API provider, online dependency install, retry, or production GUI input.

The authoritative pre-run identities, versions, gates and exact commands are in `FREEZE.json`. `run.py` contains both the no-fit X11 construction check and the one-shot formal path. `audit.py` is a distinct raw-only recomputation/mutation audit.

## Formal outcome and audit status

The one-shot CPU-only local Docker formal run completed with 10/10 color-heldout predictions correct across five seeds (all target probabilities >=0.75; all other probabilities <0.5), 16/16 base captures carrying identical `FIXTURE ITEM` text and layout, and two distinct class-specific pixel hashes. Training took 2.051 s. This is **provisional diagnostic evidence only**, not a verified/promotable result: the independent raw audit recomputed predictions and integrity successfully, but its weight-corruption negative control did not reject because the in-place NumPy `float32 + 1.0` mutation rounded back to the same float32 value. Overall audit is therefore `passed=false` (9/10 controls rejected, no integrity errors). No formal rerun or auditor patch was performed; successor audit must fix and freeze that control first.

The audit-output mount was corrected after the formal run because the original frozen audit invocation made `/out` read-only although the auditor writes `independent-audit.json`. Formal JSON and NPZ SHA-256 hashes were checked before and after audit and are unchanged. See `FREEZE.json` and `results/independent-audit.json`.

Artifacts: `results/formal-result.json`, `results/independent-audit.json`, and `results/raw_frames_and_weights.npz` (binary raw X11 frames and learned weights). The previous #2599 report remains untouched. This small synthetic setup does not demonstrate localization, transfer, GUI safety or usable computer-control capability.
