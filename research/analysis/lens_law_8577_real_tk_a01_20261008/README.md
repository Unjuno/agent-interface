# Issue #8577 A01 — real Tk widget transfer test

This additive package tests the scoped lens-law checker on actual Tk 8.6 widgets running in a disposable Xvfb display inside a locally cached, pinned WSLc image. It uses WSLc isolation and does not require Docker Desktop or an external daemon. Text setters use Tk keypress/key-release dispatch and default Entry bindings; the checkbutton uses its keyboard binding. It is a toolkit-level synthetic GUI route, not physical OS input or an application/product study. The image lacks `xauth`; use the documented direct-Xvfb route rather than `xvfb-run`.

The package preserves preregistration, frozen source/runtime hashes, construction failures, candidate raw widget state/event logs, and a separately implemented auditor. See `PROTOCOL.md`, `FREEZE.json`, `REPORT.md`, and the two outputs under `results/`.

Reproduce in Ubuntu/WSL with Xvfb and Tk installed:

The frozen image is `ai-x20-tk-5260:20261003-a02`; runtime facts and source hashes are in `FREEZE.json`. Start Xvfb directly (`Xvfb :99 ...`, then set `DISPLAY=:99`) because `xvfb-run` requires missing `xauth`. Construction commands and the one-shot formal sequence are in `PROTOCOL.md`.

Formal outputs use exclusive creation. Do not overwrite them; a new execution requires a new allocation and result directory.
