# V39 frame-signal boundary probe A01

## H / T / D / C / U

- **H:** Current V39 paired health/ammo cover monitoring does not request a new decision when a fresh observation advances and its frame hash changes while typed health/ammo and binding remain constant.
- **T:** AST-extract the frozen `DoomCoverSignalPairMonitor` implementation and its exact helper functions from main commit `f60752d0fb71595363a80977636ca74c1fd10b21`. Feed two valid typed observations: health 84 and ammo 37 at both epochs, unchanged focus/surface/geometry, increasing sequence/capture time, and different frame hashes. No application or input is launched.
- **D:** PASS if the second observation returns an invalidation requiring a new decision; FAIL if it returns no invalidation; HOLD if source identity or construction differs from the freeze.
- **C:** A changed frame hash can reflect harmless animation or viewpoint motion. This tests only the monitor's input contract; it does not decide whether a threat appeared or whether a response would be useful.
- **U:** No visual classifier, live game, model, GUI, OS input, Docker/container, or task effect was tested. This does not establish threat detection accuracy, timing, survival, or MAP01 progress.

## Result

The retained synthetic probe returned `null` for both baseline and changed-frame observations. The decision is **FAIL** for the narrow hypothesis: V39's paired health/ammo monitor did not request a new decision from frame-hash change alone. This is consistent with the current implementation, which evaluates typed health/ammo values and only compares frame hashes to detect inconsistent duplicate epochs.

This is a controller input-boundary counterexample, not a live-threat experiment. The retained Astra triage separately reports visible approaching enemies while ammo stayed at 37; it does not supply a matched stable-HUD frame sequence during a pending current-main V39 cover. The live V39 exposure remains unassigned and was not run.

## Reproduction

From the repository root:

```powershell
python research/doom/results/map01-v39-frame-signal-boundary-a01-20261005/run_probe.py
python research/doom/results/map01-v39-frame-signal-boundary-a01-20261005/audit.py
```

`FREEZE.json` identifies the source commit and blob. `raw.json` retains both monitor outputs and input identities. The audit independently checks the source object, runner hash, epoch ordering, invariant typed signals, changed frame hash, and result classification.
