# Current-main V4/V12 actual-Xvfb receipt composition A21

## Question and preregistered decision

Run exactly one lowercase `w` down/up on private Xvfb through the four exact current-main owner sources frozen by A09, and feed the unmodified admission/release return objects to the A18 frozen retained-input analyzer. `PASS_METHOD_SCOPED` requires client KeyPress/KeyRelease and independent keymap down/up, valid owner-thread release receipt, empty verified close and stopped thread, Xvfb exit zero, analyzer ready with one hold, and integrity audit. Verified X11 release with analyzer rejection is `FAIL_ANALYZER_BRIDGE`; setup issue is STOP. No retry.

This is a fresh explicit-up composition experiment, distinct from A09's close-only question and A20's older recovered V4 source. It uses Xvfb/XTEST only: no physical desktop, app/game, MAP01, model, threat, task-effect or formal/live allocation.

## Frozen conditions

- Current-main owner files copied byte-for-byte from `v39_owner_close_currentmain_a09_20261012/SOURCE` committed in PR #8874 at head `6d008b53e23fda4703c8f56c4ea1bd762e5d147b`; A09 froze current main `f185a9059d485a4f8d5a65e9e7f6782897f67eae`.
- Analyzer is the unchanged A18 copy from PR #8857 head `4536ebff7d71848dc86fbf1cdc4f54957eb9ce2d`.
- WSLc 3.0.1.0; image `sha256:d3e433793e1b6a0bc9fb821b0aa2648945aaf7ba91c3ecc4b8b74b5123d76592`; Python 3.14.8 linux/amd64.
- `--pull never --network none --cpus 1 --memory 512M --user 65534:65534`, source read-only, output separate and writable, `--rm`. Swap/cgroup hard limit unavailable.
- Candidate runs once in `results/a21-01/raw.json`, container `codex-wslc-pr8874-xvfb-a21-20261013`.

A20 remains separately preserved. A20 used the PR's `actual_source_recovery` snapshot, whose V4 does not populate `owner_transition_verified`; A21 uses A09's exact current-main freeze.
