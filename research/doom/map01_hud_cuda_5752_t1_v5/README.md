# MAP01 HUD CUDA allocation 05

This additive package is a fresh, host-only successor to Issue #5752 allocation-04. Allocation-04 remains unchanged as `STOP_INSUFFICIENT_DISK_SPACE`; its candidate count was zero, so allocation-05 does not retry a consumed scientific run.

The experiment uses the exact 23 retained v38/v39 screenshots, source report/event files, CPU HUD reader, and pinned Freedoom WAD defined by `dataset.json` and `FREEZE.json`. It tests exact CPU/CUDA health and ammunition reader parity and a preregistered warm per-frame speed threshold. It does not use a game, model/provider, Docker, WSL, GUI, OS input, or synthetic replacement data. It is method-construction/measurement evidence only and does not close Issue #59.

Before formal execution, run the CPU construction tests and verify the complete input/source inventory. The only formal window is 2026-10-01 10:20–10:40 UTC, on the Windows host RTX 3080. At the start, refresh main, queue, process/GPU and disk state, and refreeze to exact current main. Candidate invocation limit is one; independent CPU-only auditor limit is one after candidate exit 0; retries are zero. Any failed gate is a retained STOP/NOT_EVALUATED.

The 23 PNGs and four report/event inputs are not duplicated into this package. Reproduce their `data/` layout from the immutable retained source directories `research/doom/results/map01-v38-integrated-threat-live-01/` and `research/doom/results/map01-v39-coast-liveness-live-01/`, following the exact file list and hashes in `dataset.json`. Use only the already-local Freedoom 0.13.0 WAD with the exact `FREEZE.json` SHA-256; no download or substitute is allowed. Do not overwrite a differing existing input.

The allocation's H/T/D/C/U, commands, and acceptance gates are in `PREREGISTRATION.md`. Historical raw outcomes and all source inputs remain immutable.

