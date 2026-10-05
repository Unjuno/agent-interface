# Current-head V15 per-key owner identity recheck

This follow-up reruns the previously reported V15 per-key owner-selection probe against PR #8065's latest head, `4158d9b063e7cbf56828f1b0667ec2714af0ff2b`, based on current main `11445a7ca200404ddc80bf7ebb1dbef86eb059de`.

The bundled Python run reproduced the mismatch: V12-perkey selected the archived A01 owner; default V15 selected the current V4 transition owner; V15-perkey selected current raw `research/live_control/input_owner_v12.py`, while the source manifest recorded the archived A01 owner hash. The startup selection boundary completed in all three routes, but no session or owner was instantiated. The probe's Xlib, VizDoom, process, and thread constructors were replaced with fail-fast stubs.

The first attempt with system Python stopped before the boundary because Pillow was unavailable. That STOP is retained. The same frozen probe and source closure then ran successfully with the desktop-bundled Python 3.12.14 / Pillow 12.3.0. No dependency was installed.

This is source-selection evidence only. It establishes no KeyRelease, server keymap state, physical release, application consumption, live game/input, threat reaction, task effect, recovery, or MAP01 outcome. The source-derived missing-UP concern in PR #8079 remains distinct from the executed startup selection result.

See `PLAN.md`, `FREEZE.json`, `source-manifest.json`, `source-snapshots/`, `results/`, and `audit.py`. The candidate was reconstructed exactly from the frozen PR head and independently audited without importing the probe.

## Reproduction

Use CPython 3.12 with Pillow available. The retained run used the Codex desktop bundled Python 3.12.14 / Pillow 12.3.0 recorded in `RUN.json`.

```sh
git fetch origin pull/8065/head:refs/remotes/origin/pr8065
python3 -B audit.py
python3 -B replay_startup.py /tmp/v39-owner-recheck-new-output
```

The replay refuses an existing output directory. It materializes the 56 retained exact snapshots, launches three fresh processes, and stops before owner/session construction. Two snapshots are base64-encoded solely to preserve exact source bytes while keeping `git diff --check` clean; the replay decodes and verifies each frozen SHA-256 before use.

## Current-main relevance check

Main has advanced to `1fa854d537bfd711b5dfd99f8c04ab6c35bad286` since the tested PR head was frozen. `CURRENT_MAIN_RECHECK.json` records a byte comparison of the 56-path probe closure against candidate base `11445a7ca200404ddc80bf7ebb1dbef86eb059de`: all 55 shared source paths are unchanged; the sole candidate-only path is `research/doom/v39_measurement_backend_selection_v1.py`. The independent auditor checks this comparison. The original failed v0 comparison and audit remain as previews; v1 classifies the helper as candidate-only.
