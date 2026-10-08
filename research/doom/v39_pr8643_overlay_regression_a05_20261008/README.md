# PR #8643 pending-observation suite overlay validation A05

## H / T / D / C / U

**H.** The recovery changes in PR #8643 should preserve the existing bounded drain and invalidation behavior across the directly affected regression suite, including fail-closed handling when stale initial-cover submission receives no newer full observation, under both normal Python and optimized Python execution.

**T.** Freeze PR head `80d9d74b8557936984c040ddb3729436bdbe9d0d` and dependency base `1f81daa690b567a9a049cc75fae8619b2660c343`. Extract only the seven candidate files listed in `FREEZE.json` into a temporary source overlay. Before running, verify that the checked-out dependency tree differs from the base only under the listed evidence output prefixes. Run the candidate `test_map01_v39_pending_observation_drain.py` against unchanged dependencies from the base, once normally and once with `-O`. Record raw stdout/stderr and exit codes.

**D.** PASS if all seven overlay blobs match their frozen Git identities and both test runs exit zero with 15 tests reported. Otherwise FAIL/HOLD with the first retained output.

**C.** The runner overlays changed controller/test/admission/guard files while importing other modules from the pinned base checkout. The suite uses deterministic fixtures; this is not a full source checkout or live execution.

**U.** No full controller session, App Server, model, game, GUI, OS input, physical release measurement, or task effect is run. Passing these 15 tests supports the selected drain/recovery integration contracts only; Issue #59's live threat and task-effect gates remain open.

## Result

PASS. Both normal and optimized Python 3.13 runs completed 15/15 tests, including fail-closed timeout handling when stale initial-cover submission receives no newer full observation. The dependency checkout had no changes outside the listed experiment packages. The temporary overlay was removed by its context manager after the runs. Candidate file hashes and raw output are retained in `FREEZE.json`, `normal.*.txt`, `optimized.*.txt`, and `RESULT.json`.

## Reproduction

From the repository root:

```powershell
py -3.13 -B research/doom/v39_pr8643_overlay_regression_a05_20261008/run_suite.py
py -3.13 -B research/doom/v39_pr8643_overlay_regression_a05_20261008/audit.py
```

The runner needs only a small temporary overlay; it does not materialize a full worktree.
