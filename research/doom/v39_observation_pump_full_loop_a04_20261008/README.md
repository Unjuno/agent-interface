# V39 pending-loop full-body construction A04

This one-shot successor corrects the predecessor's healthy schedule: each scripted terminal ID matches the currently active cover, including both renewals. It pins current main and executes the exact nested `wait()` and complete pending-future loop AST, plus production monitor, terminal validator, and cancellation helper. Only planner/process and cover-submission boundaries use deterministic fakes.

## H / T / D / C / U

- **H:** The current-main loop dispatches typed observations across two matching cover renewals while the planner remains pending, stops renewing when completion is observed, and cancels the active cover before planner interrupt transport on hard invalidation.
- **T:** Execute the frozen AST slices with three matching healthy terminal IDs and scripted completion; execute a separate hard-invalidation sequence.
- **D:** PASS only if three terminals are validated, exactly two renewals occur before the done poll and none after, every healthy observation reaches the monitor while pending, and invalidation produces cancel write/flush before interrupt transport followed by verified empty release.
- **C:** Synthetic queue, deterministic planner/process fakes, and patched cover submission; these do not exercise producer timing or the outer session process.
- **U:** No HUD accuracy/cadence, useful feedback, wall-clock behavior, live input release, recovery, survival, progress, or task outcome.

Source identities are pinned in `FREEZE.json`. The one-shot candidate writes `RESULT.json` and `events.jsonl` and refuses overwrite. The read-only audit verifies source identities and decision gates.

Reproduction:

```text
python research/doom/v39_observation_pump_full_loop_a04_20261008/candidate.py
python research/doom/v39_observation_pump_full_loop_a04_20261008/audit.py
```
