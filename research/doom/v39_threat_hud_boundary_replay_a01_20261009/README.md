# Current-main replay of the retained V39 threat/HUD boundary

## H/T/D/C/U

**H.** Replaying the retained live MAP01 paired typed observations from source sequence 166 through the frozen `main` V39 monitor will preserve the authored cover at sequence 200 where health equals the derived hard floor (51), then invalidate at the first later paired observation below that floor, sequence 218 (health 48, ammo 37). The invalidation must request a new decision and grant no input authority.

**T.** `FREEZE.json` pins `main` commit `743ae74ec5be2472ff27fa06fe13d5ecf8534de5`, the controller Git blob and SHA-256, retained event/report hashes, and the three boundary PNG hashes. `replay.py` feeds the 52 post-source `typed_observation` rows through the production `build_cover_monitor()` and `DoomCoverSignalPairMonitor`; `audit.py` independently derives the earliest hard crossing from raw event rows and checks the output, source identity, PNG bytes, and terminal planner record. The screenshots were directly inspected only for descriptive scene labels; image labels do not influence the replay.

**D.** PASS only if all 52 rows are contiguous and paired, sequence 200 has no invalidation at equality, sequence 218 is the first hard invalidation with `health:below_hard_minimum`, the model answer is interrupted/ineligible, and no input authority is granted. Any identity mismatch or deviation is STOP/FAIL.

**C.** The retained trace has a protocol scope of its own and predates the current V15/V12 startup closure. This replay tests the current-main guard logic against historical typed rows, not the live producer, controller lifecycle, or current V15 input stack. A threshold guard may react to damage while being unable to classify a visible enemy before HP/ammo changes.

**U.** This is one retained trajectory, not a new allocation or causal comparison. It does not establish the first threat-appearance time, whether the authored cover was inappropriate at sequence 200, physical per-key release timing, independently useful feedback, recovery efficacy, survival benefit, or MAP01 completion. The screenshots show a hostile in view at sequence 200 and a hostile firing with damage overlay at 218, but those visual observations are not a validated threat classifier.

## Result

The current-main replay processed 52 post-source observations. Sequence 200 preserved the cover at health 51/ammo 38; the first hard crossing was sequence 218 at health 48/ammo 37, classified as `health:below_hard_minimum`. The planner answer became ineligible and input authority remained false. Sequence 200 was captured 5,536.881520 ms after the model turn started; sequence 218 followed 3,185.812619 ms later. The planner terminal was observed 193.075675 ms after the sequence-218 capture. These are timestamps from one historical trace, not response distributions or guarantees.

The practical finding is that a threat can be visually present while the current typed guard remains at equality and preserves cover; the guard's first stop is tied to a later HUD threshold crossing. This supports testing an earlier threat cue under fresh live exposure, but it does not justify a full-frame-hash cancel rule: the existing A14 posthoc trace found whole-frame changes on every adjacent pair, mostly with unchanged health/ammo, without proving those changes were task-relevant.

The exact source-local regression selection (`test_map01_overlap_controller_v39`, `test_map01_overlap_controller_v39_dual_signal`, and `test_map01_overlap_controller_v39_pair_duplicate_consistency`) passed 36/36 in normal and optimized Python after redirecting temporary files from full C: to D:. The prior C: `WinError 112` setup stop is retained above.

The first candidate launch stopped because its sequence selector assumed the source row shared the later cover ID; the next stopped because the frozen row count omitted the source observation. Both were harness construction errors before scientific evaluation. A subsequent audit stop came from resolving the repository root one level too high; the candidate's original root calculation was correct. A later audit also required the candidate to serialize the frozen Git blob. These setup outcomes are preserved in `CONSTRUCTION_NOTES.md`; the corrected candidate/audit pair is under `reproduction-06/`. They do not count as experimental outcomes.

## Reproduction

From repository root:

```powershell
python research/doom/v39_threat_hud_boundary_replay_a01_20261009/replay.py --output research/doom/v39_threat_hud_boundary_replay_a01_20261009/reproduction-06/RESULT.json
python research/doom/v39_threat_hud_boundary_replay_a01_20261009/audit.py --result research/doom/v39_threat_hud_boundary_replay_a01_20261009/reproduction-06/RESULT.json --output research/doom/v39_threat_hud_boundary_replay_a01_20261009/reproduction-06/AUDIT.json
```

No Doom process, model, GUI, OS input, GPU, container, or live allocation was started. The live V39 threat/recovery gate remains open and unassigned.
