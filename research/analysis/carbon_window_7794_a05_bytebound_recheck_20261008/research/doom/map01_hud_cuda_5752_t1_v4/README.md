# MAP01 HUD CUDA allocation 04

This is an additive, preparation-stage source package for Issue #5752. It tests the exact CPU-vs-CUDA WAD-template HUD reader on the 23 retained v38/v39 screenshots described in `PREREGISTRATION.md`. It is not live control evidence and does not close Issue #59.

- Reserved host-only RTX 3080 window: 2026-10-01 08:05–08:15 UTC.
- Candidate count: at most one; separate raw-only auditor only after candidate exit 0; no retry.
- The formal gate must refetch current main and refreeze if it differs from `FREEZE.json`.
- Candidate/auditor use no Docker, model/provider, network, game, GUI, OS input, or task effect. The tested inner CUDA run is executed directly on the authorized Windows host.

## Input staging

`dataset.json` records paths relative to the local package's `data/` directory. The package deliberately does not duplicate the retained PNG/report/event inputs or the 28 MB WAD. Before the formal window, stage from the exact frozen repository source tree, preserving this package layout:

- `research/doom/results/map01-v38-integrated-threat-live-01/`
- `research/doom/results/map01-v39-coast-liveness-live-01/`

Copy the selected `runtime/*.png`, `runtime/events.jsonl`, and `report.json` files under matching `data/map01-.../` paths. Verify all 23 image SHA-256 values and all four report/event byte counts and SHA-256 values in `dataset.json` before candidate launch. Use the already-local Freedoom 0.13.0 WAD only if it matches `FREEZE.json` exactly; no network download or substitution during the allocation. Never copy files over an existing differing input.

## Preparation checks

The local construction suite is `python -m unittest test_hud_failure_evidence -v`; the PowerShell gate suite is `powershell -NoProfile -ExecutionPolicy Bypass -File gate_correction/test_gpu_preflight_gate.ps1`. These are preparation checks, not CUDA results. At formal start, rerun the source/hash, output-empty, 64 MiB disk-reserve, GPU process, queue and branch/path collision gates and capture their raw outputs.

See Issue #5752 for the hypothesis, limits, STOP history and allocation log.
