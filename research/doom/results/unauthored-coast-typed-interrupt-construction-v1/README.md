# Unauthored-coast typed-interrupt construction candidate v1

This package records a controller-boundary construction result for Issue #59. It does not alter the retained v39 controller, raw allocation, or report.

## H/T/D/C/U

- **Hypothesis:** During an input-free, unauthored coast, a sufficiently large bound health decrease can make an in-flight model answer stale before it finishes. A typed event can signal that change before its matching screenshot artifact is published.
- **Treatment:** Candidate v40 subscribes only the unauthored empty coast to early typed health events. A six-point loss is the *exploratory candidate threshold* derived post hoc from one retained v39 trace. A crossing cancels the model and coast; the existing verified-empty-release check remains mandatory. Before replanning, the controller uses an already-drained matching/newer screenshot or waits for one. Authored guards and normal fresh action admission are unchanged.
- **Decision:** Construction boundary passes: Python syntax compilation and 10 focused unit tests pass (7 monitor/handoff, 3 controller integration). The tests cover threshold crossing, sub-threshold coalescing, unknown health, authority non-escalation, authored-path preservation, release-before-return, and both screenshot ordering races.
- **Control:** Historical v39 remains byte-for-byte unchanged. Its existing fresh final action admission remains the authority gate. The retained raw trace is `research/doom/results/map01-v39-coast-liveness-live-01/runtime/events.jsonl` (blob `cbaeed9c7ba27b53cef9d10730ae33313371ad9a`); this construction did not rerun or modify that allocation.
- **Uncertainty:** The six-point threshold is post-hoc and unvalidated. This construction does not establish saved model time/tokens, reduced risk, improved survival, useful task feedback, recovery efficacy, matched tempo, or game completion. No new model/game/live allocation was run. Keep v40 a review candidate until a separately frozen prospective evaluation and lane/allocation authority are available.

## Reproduction

From the repository root, with the research Python dependencies available:

```powershell
python -m py_compile research/doom/map01_overlap_controller_v40.py research/doom/unauthored_coast_liveness_v1.py
python -m unittest research.doom.test_unauthored_coast_liveness_v1 -v
python -m unittest research.doom.test_map01_overlap_controller_v40 -v
```

Observed result in the construction workspace: compile exit 0; 7/7 monitor/handoff tests and 3/3 controller integration tests pass.
