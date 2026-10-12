# Typed health handoff and held-input occupancy

## Result

In a 10-pair WSLc CPU construction comparison, immediate typed-health handling reduced fake-X key-down-to-verified-owner-release time by a median **148.408 ms** versus delaying delivery by 150.031473 ms. Median durations were 2.071 ms (immediate) and 150.484 ms (delayed); every pair favored immediate handling (minimum paired reduction 148.319 ms). All 20 runs produced the same health `HARD_INVALIDATED` result, requested Executor cancellation before planner interruption, verified an empty owner release, left no fake keys/buttons down, and rejected the pending planner answer.

This isolates one effect: when the typed signal reaches the monitor, the existing cancellation and owner-release path can remove roughly the injected artifact-wait period from held-input occupancy in this synthetic composition. The delayed arm injects a wait; it does not run the native image artifact pipeline. The result supports preserving and validating early typed handoff, but it does not prove that the full controller process delivers these events with the same timing or improves game outcomes.

## Reproduction

From this directory in PowerShell, with WSLc and the frozen image already available locally:

```powershell
.\run_registered_pairs.ps1
python .\audit.py
```

The source snapshot under `worktree/` contains the exact controller helpers, PR #8866 monitor, Executor V13, owner V4→V3→V12 and fake-X fixture used by the harness. `FREEZE.json` identifies all frozen source/input files and the immutable Python image digest. `PREREGISTRATION.md` records the hypothesis, two arms, 10-pair alternating order, criteria and stop rule. Smoke runs are separate and excluded.

## Evidence and limits

- The delay (150.031473 ms) is the maximum `typed_emit_to_artifact_ready_ms` in the retained 218-observation report at `inputs/source-report.json` (SHA-256 `719db21040b843c5c91c5ff1f3d9fb2051ae1f1e008971547f39f015b4337687`).
- `results/` retains each raw result JSON, WSLc stdout/stderr log, run order, and independent audit.
- WSLc emitted that swap-limit support is unavailable. The configured 1 CPU/512 MiB limits and warning are preserved; this report does not infer full cgroup or swap enforcement.
- Fake X is in-memory. No physical input, GUI, game, live allocation, useful feedback, threat response, survival, task success, or successful bounded recovery was tested.
- The decisive #59 gate remains a separately authorized fresh threat-exposure run on the integrated real-time path. This construction result does not consume or authorize that allocation.
