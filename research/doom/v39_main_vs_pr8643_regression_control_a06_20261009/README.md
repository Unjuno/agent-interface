# V39 current-main versus PR #8643 regression control A06

## H / T / D / C / U

**H.** PR #8643's new controller cases should distinguish its recovery changes from current main: current main should reuse a stale remaining cover after partial-action discard and lacks the pre-planner initial-cover cancel/release helper; the candidate should pass both cases.

**T.** Freeze current main `5cfe661826c5742eb26da2ba9a9304ae0cb480d4`, candidate PR #8643 `38569db07352a8d42e08fd6711ba32c77aca20a4`, and dependency base `1f81daa690b567a9a049cc75fae8619b2660c343`. Overlay the current-main controller, candidate's exact controller test file, and only the controller's statically import-reachable direct Python modules from the current-main commit. Verify each extracted blob and SHA-256. Run the nine controller regression tests normally and with Python `-O`. Compare with the A05 retained candidate run, whose same nine tests passed in both modes.

**D.** The control is discriminating if current main reproduces exactly one stale-cover assertion failure and one missing pre-planner cancellation method error in both modes, while the same candidate tests report 9/9 PASS in A05. Any other count or failure pattern is UNEXPECTED.

**C.** Test fixtures isolate controller contracts and the temporary overlay uses the main dependency sources retained at the pinned base. The experiment tests that the candidate regression cases catch the targeted current-main behavior; it does not measure runtime frequency or user-visible effect.

**U.** No Doom process, model, GUI, OS input, live threat exposure, key release measurement, or task-effect endpoint was used. This evidence does not authorize merging PR #8643 or satisfy Issue #59's live gate.

## Result

**DISCRIMINATING_BASELINE.** Current main ran all nine tests, with seven passing, the stale remaining-cover reuse assertion failing, and the pre-planner cancel test erroring because `cancel_initial_cover_before_planner` is absent. The result reproduced under normal and optimized Python. A05's exact candidate test file passed 9/9 in both modes against candidate controller `38569db`. Thus the tests detect two concrete current-main gaps addressed by PR #8643; this is a source/fixture result only.

The initial wide-import prototype (`RESULT_WIDE_IMPORT_V0.json`, `wide_import_v0.*.txt`) extracted 1,992 top-level Python files and reproduced the same disposition. It is retained as an exploratory execution record; the final runner narrows extraction to the import-reachable closure and reruns the frozen controller cases.

## Reproduction

```powershell
py -3.13 -B research/doom/v39_main_vs_pr8643_regression_control_a06_20261009/run_control.py
py -3.13 -B research/doom/v39_main_vs_pr8643_regression_control_a06_20261009/audit.py
```
