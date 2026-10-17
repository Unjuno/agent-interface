# V39 retained model-pending signal trajectory, posthoc A01

## H / T / D / C / U

**H.** The retained `map01-v39-coast-liveness-live-01` episode has 218 typed HUD observations and six planner-pending windows. A reproducible reconstruction should join each decision's source image to its full observation, use that decision's `planner_terminal_observed_ns` as the window end, and retain every health/ammo transition.

**T.** Read the immutable report, event, delivered, and scorer Git blobs pinned in `FREEZE.json`. Verify SHA-256 and byte lengths; reconcile each typed row against its full observation and signal pair; reconstruct all six source-to-terminal windows; then independently audit the authored health-guard boundaries and scorer disposition. Do not rerun or modify the game, model, GUI, controller, or historical episode.

**D.** PASS requires byte-identical event/delivered streams, 218 contiguous typed sequences paired to 218 full observations, exact agreement with all six frozen transition tables and terminal sequences, guard floor/equality/crossing agreement with the report, and mutation rejection by tests/auditor.

**C.** Health declined in five of six pending windows. Ammo declined in three of six windows (decisions 1, 4, 5), using each window's admitted source sample through its planner terminal. During the active authored cover in decision 1, health reached floor 85 at seq62 and remained equal to it through seq70; equality is soft under the strict `< hard_minimum` rule, and no invalidation was reported. Decision 4's floor was 55; seq154 health 61 was above it. In decision 5, health equalled floor 51 from seq200 through seq217, then first fell below it to 48 at seq218; the report records invalidation at seq218. The scorer records one kill, zero deaths, no MAP01 exit, and an unfinished episode.

**U.** Health/ammo are template-derived HUD values, not independent game-state ground truth. These timestamps are a posthoc reconstruction and do not establish causality, whether the cover policy caused damage, or whether interrupting at equality would improve control. The pinned commit identifies the retained data blobs; it does not identify the exact controller source used for the historical episode. This is not a fresh current-main live run, useful-recovery result, or MAP01 completion.

## Reconstructed windows

| Decision | Source seq, health/ammo | Last typed seq before planner terminal | Health/ammo changes from source |
|---:|---:|---:|---|
| 0 | 1, 97/48 | 28 | none (97/48) |
| 1 | 36, 97/46 | 70 | 37: 91/46; 47: 91/45; 62: 85/45; 64: 85/44 |
| 2 | 70, 85/44 | 91 | 76: 82/44; 81: 76/44; 90: 73/44 |
| 3 | 91, 73/44 | 113 | 97: 72/44; 103: 68/44 |
| 4 | 115, 65/43 | 159 | 125: 65/42; 143: 65/41; 144: 64/41; 154: 61/41 |
| 5 | 166, 61/40 | 218 | 167: 55/40; 177: 55/39; 193: 52/39; 194: 52/38; 200: 51/38; 212: 51/37; 218: 48/37 |

The table lists only changed pairs after the source row. The exact timestamps, unchanged samples, model timing fields, hashes, and guard rows are in `RESULT.json`. The six `model_ns` durations are 8.452, 5.720, 6.307, 6.725, 7.198, and 8.916 seconds; the capture-to-terminal windows are separately recorded.

## Reproduce

Inputs are not duplicated: `FREEZE.json` pins the existing report and raw JSONL/score blobs by commit, Git blob ID, byte length, and SHA-256. The scripts read those exact Git objects with `git show`, so image artifacts and a mutable worktree copy are not needed.

From the repository root, run the tests in normal and optimized Python:

```sh
python -B -m unittest discover -s research/doom/v39_retained_pending_signal_trajectory_posthoc_a01_20261008/tests -v
python -B -O -m unittest discover -s research/doom/v39_retained_pending_signal_trajectory_posthoc_a01_20261008/tests -v
```

To reproduce the result without overwriting the retained `RESULT.json`, choose a new output path that does not already exist:

```sh
python -B research/doom/v39_retained_pending_signal_trajectory_posthoc_a01_20261008/analyze.py --output /tmp/v39-trajectory-reproduced.json
python -B research/doom/v39_retained_pending_signal_trajectory_posthoc_a01_20261008/audit.py /tmp/v39-trajectory-reproduced.json
```

`analyze.py` refuses to overwrite an existing output file. `audit.py` independently rereads and validates the pinned raw Git blobs; it does not modify the candidate or frozen inputs.