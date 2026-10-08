# Current-main hard-invalidation → fresh-replan composition probe

This construction-only check composes exact functions from current `main` at `9331b399d12d60c3f8a9d694d3c5ad219d7d86c4` to test a gap between the existing unit boundaries: when a typed HUD hard invalidation arrives during a pending planner turn, can local input cancellation precede a deliberately blocked planner-interrupt acknowledgment, can the consumer retain the paired full image while waiting for executor terminal, and does the next planner input use that fresh frame and HUD?

## H/T/D/C/U

**H — Hypothesis.** Under the current V12 producer/executor ordering, a hard typed observation during a pending plan causes the current controller helper to flush executor cancel before the remote interrupt response can block. The old plan remains ineligible even if the server reports completion, and the consumer's matching full observation becomes the next source after a neutral terminal.

**T — Test.** An inert queue/client/executor schedule calls the current-main AST-extracted `DoomCoverSignalPairMonitor`, nested `wait`, `cancel_invalidated_cover`, `begin_model_turn`, and `temporal_sheet`; it uses the exact current-main `PersistentPlannerAdapter` and `doom_source_refresh_v1.refresh_source`. Sequence 10 is the old source (health 70/ammo 8). Sequence 11 is a typed hard invalidation (health 60 below floor 65), followed by its matching full image and a cancelled terminal with verified empty keys/buttons. The fake planner blocks interrupt acknowledgment, then reports a completed stale answer to exercise the completion race. The next source and temporal sheet must use sequence 11 and the next planner request must include fresh health/ammo and the new image.

**D — Decision.** PASS requires `executor_cancel_write → executor_flush → planner_interrupt_request → planner_interrupt_ack`, verified empty release, ineligible/null old answer, source refresh selecting sequence 11, and a second turn carrying the temporal sheet whose newest tile is the fresh synthetic frame. Any ordering change, admitted stale answer, old source, unverified/nonempty release, or wrong image/HUD is FAIL.

**C — Competing explanation.** The deterministic event fixture may omit an integration interaction in `main()` or an OS/App Server scheduling effect. The current backend source emits typed evidence, publishes the image, and emits the matching full observation before the snapshot returns; V12's inherited executor emits terminal only after backend execution and release cleanup. This makes the chosen queue order representative of that source route, but does not reproduce its timing.

**U — Limits.** The test does not run controller `main()`, an App Server, a model, a Doom process, OCR over a real screenshot, GUI observation, OS input, or physical release. Guard evaluation uses a fake floor guard; typed evidence values and image bytes are synthetic. It establishes a source-function composition property only. It does not establish enemy recognition, gameplay benefit, bounded live cancellation latency, useful feedback, recovery, survival, or MAP01 completion. Issue #59 remains open. A04 is a real bounded live threat exposure but has a staged-source provenance HOLD; it did not show an authored active-cover health-change interrupt or useful recovery. This probe neither reruns A04 nor uses a live allocation.

## Result

One composed case passes normally and under `python -O`. The stale planner turn completes at the fake server but is rejected by the real adapter as `answer_eligible=false`. The executor cancel is written and flushed before the blocked interrupt request. The current-main wait closure retains full observation sequence 11 before returning the matching empty-release terminal; the actual source-refresh function accepts that observation and the actual temporal-sheet/model-input functions place the fresh frame and HUD values in the next turn.

Raw stdout/stderr and exit codes are in `normal.*` and `optimized.*`; the structured event record is `result.json`. `audit_probe.py` independently checks source Git blob hashes, producer ordering, result invariants, and raw run exits. `SHA256SUMS.txt` inventories the package.

## Reproduction

From this directory:

```powershell
python test_invalidation_replan_composition.py
python -O test_invalidation_replan_composition.py
python audit_probe.py
```

The exact public source snapshot and GitHub main SHA are retained in `FREEZE.json`; the evidence code reads the bundled local source copies when present and otherwise resolves the verified files from the repository checkout. No production file was edited.
