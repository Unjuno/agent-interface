# Typed health handoff and held-input occupancy

## Result

In a 10-pair WSLc CPU construction comparison, immediate typed-health handling reduced fake-X key-down-to-verified-owner-release time by a median **148.408 ms** versus delaying delivery by 150.031473 ms. Median durations were 2.071 ms (immediate) and 150.484 ms (delayed); every pair favored immediate handling (minimum paired reduction 148.319 ms). All 20 runs produced the same health `HARD_INVALIDATED` result, requested Executor cancellation before planner interruption, verified an empty owner release, left no fake keys/buttons down, and rejected the pending planner answer.

This isolates one effect: when the typed signal reaches the monitor, the existing cancellation and owner-release path can remove roughly the injected artifact-wait period from held-input occupancy in this synthetic composition. The delayed arm injects a wait; it does not run the native image artifact pipeline. The result supports preserving and validating early typed handoff, but it does not prove that the full controller process delivers these events with the same timing or improves game outcomes.

## Context from the retained live trace

The same retained MAP01 episode has a hard health event at sequence 218 while `cover-5` was running. The accepted cover contained 16 steps; the event arrived at step 11 with health 48 below hard minimum 51. The exact 634-row event log is preserved at `inputs/runtime-events.jsonl` and its SHA-256 is authenticated by the retained manifest (`2c917658e8bba0a94e5a34f0ee3d968553cd56950105196871012f2e3eedb381`). The prior corrected audit records `dynamic_revocation_exposed=true` for this one episode.

The typed event emitted 15.780 ms after capture. Artifact readiness followed 111.119 ms later; the full guard received the event 117.910 ms after typed emission. It cancelled the cover; the owner verified an empty key/button state 32.062 ms after monitor receipt, and the cancelled cover terminal followed. The planner turn then ended interrupted with its answer ineligible. This is direct evidence that the retained integrated MAP01 path once cancelled a running cover and verified release on a hard health invalidation. The terminal was 13.140 ms before the planner terminal.

Two limits remain. The log does not snapshot an individual key as down immediately before this event, so the empty release receipt alone does not prove that a physical key was held at that instant. This was one finite episode, not repeated reliability evidence; it did not exit MAP01. The 10-pair comparison above is still a synthetic in-memory fake-X test of the latency potentially removed by early typed dispatch; it did not replay the live game event or the native artifact pipeline.

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
- The paired comparison uses in-memory fake X; it does not itself exercise physical input, GUI/game feedback, survival, or recovery. The retained one-off MAP01 trace supplies a scoped live cancellation/release observation, but not MAP01 exit, repeated reliability, or successful bounded recovery.
- The experiment result is recorded on [Issue #59](https://github.com/Unjuno/agent-interface/issues/59#issuecomment-6118247767). A correction to the retained-event interpretation is recorded [here](https://github.com/Unjuno/agent-interface/issues/59#issuecomment-6118323112) and preserved in `RETAINED_EVENT_CORRECTION.md`. Issue #59 remains open; a fresh bounded run is still needed to test repeatability and task outcome. This work does not consume or authorize a new live allocation.

