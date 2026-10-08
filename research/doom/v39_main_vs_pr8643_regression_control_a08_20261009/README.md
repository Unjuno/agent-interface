# V39 current-main versus latest PR #8643 regression control A08

## H / T / D / C / U

**H.** The latest 15 controller tests in PR #8643 should continue to distinguish its recovery changes from current main: the three A07 baseline regressions should recur, while the candidate should pass the expanded stale-initial-cover caller and ACK observation-replay cases.

**T.** Freeze current main `5cfe661826c5742eb26da2ba9a9304ae0cb480d4`, candidate PR #8643 head `8c0aad30ba99381871a88c811a9ec55507936ee4`, and dependency base `1f81daa690b567a9a049cc75fae8619b2660c343`. For each arm, extract its exact controller and static import closure, plus the same candidate 15-test controller file. Run normal and optimized Python in isolated temporary overlays.

**D.** PASS for the differential if the three predeclared A07 regressions recur on main in both modes and the candidate runs all 15 tests successfully in both modes. Additional main failures remain reported and do not change that predeclared criterion.

**C.** Deterministic fixtures test stale-source recovery and ACK observation replay contracts. This distinguishes the candidate snapshot from current main; it does not measure live runtime frequency or task benefit.

**U.** No Doom process, model, GUI, OS input, live threat exposure, physical key release, or task-effect endpoint was used. This does not authorize merging PR #8643 or satisfy Issue #59's live gate.

## Result

**DISCRIMINATING_BASELINE.** Current main reported 1 assertion failure and 7 errors across 15 tests in both modes. The three predeclared regressions recurred, and all five new follow-up cases also failed to execute their required candidate paths on main. Candidate head `8c0aad3` passed all 15/15 tests in normal and optimized Python. The detailed outcomes and source identities are in `RESULT.json` and the raw logs.

After execution, PR #8643 advanced to `cae208b3ab11417ebcebb9d7097cade9b6aea295`. The tested controller and controller-test blobs are unchanged from A08's candidate snapshot; only the separate pending-observation drain test file changed. The current PR replay gate and workspace index pass; its native MCP check is still pending. See `LATEST_HEAD_RECHECK.json` for the exact blob comparison and statuses.

## Reproduction

```powershell
py -3.13 -B research/doom/v39_main_vs_pr8643_regression_control_a08_20261009/run_comparison.py
py -3.13 -B research/doom/v39_main_vs_pr8643_regression_control_a08_20261009/audit.py
```
