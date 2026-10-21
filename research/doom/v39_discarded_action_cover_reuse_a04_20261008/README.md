# Discarded remaining action and cover reuse A04

## H / T / D / C / U

**H.** After a multi-segment action partially completes and a later segment is rejected as stale, its prior receipt can still say `model_action_discarded=false` while `remaining_action_discarded=true`. Current main's `reusable_cover` may then reuse a cover authored for an action whose remainder was discarded. The candidate predicate should suppress that reuse while preserving valid completed and legacy decision records.

**T.** Freeze current main `1f81daa690b567a9a049cc75fae8619b2660c343` and PR #8643 candidate `7221ec319cc11f660cbba39900eb12c4c409845b`. AST-extract the exact `reusable_cover` functions. Compare one partial-stale receipt against completed and legacy controls.

**D.** PASS if main reproduces stale cover reuse, candidate returns no cover for the discarded remainder, and candidate retains valid reuse for completed and legacy records. Otherwise FAIL or HOLD on source mismatch.

**C.** The synthetic receipt represents a concrete state written by stale-rejection handling. This is a finite deterministic branch result; it does not measure how often the state occurs or verify downstream execution.

**U.** Only the exact predicate is evaluated. No full controller, monitor, planner, app, model, OS input, physical release or live task is run. This is a local correctness result for cover selection, not a live recovery or task-effect claim.

## Result

PASS. At the pinned main commit, the partially completed action's remaining stale cover was reused. At candidate `7221ec3`, the same record returns no cover; completed and legacy control records preserve established reuse behavior. Source identities, run output, independent audit and focused test are retained in this directory.

## Reproduction

```powershell
py -3.13 -B research/doom/v39_discarded_action_cover_reuse_a04_20261008/run_experiment.py
py -3.13 -B research/doom/v39_discarded_action_cover_reuse_a04_20261008/audit.py
py -3.13 -B -m unittest discover -s research/doom/v39_discarded_action_cover_reuse_a04_20261008 -p test_cover_reuse.py -v
```
