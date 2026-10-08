# PR #8643 current affected-suite regression A09

## H / T / D / C / U

**H.** The latest PR #8643 changes to V39 controller recovery, pending-observation draining, final-action admission, and running-action guards should preserve all directly affected controller and guard regressions under normal and optimized Python.

**T.** Freeze PR #8643 head `cae208b3ab11417ebcebb9d7097cade9b6aea295` and dependency base `1f81daa690b567a9a049cc75fae8619b2660c343`. Build a temporary overlay from the four selected test files and their statically import-reachable Python source modules, all extracted from the frozen candidate. Run each suite normally and with `-O`; retain raw stdout/stderr and exact source blob/SHA-256 identities.

**D.** PASS if controller (15), pending drain (20), final-action admission (9), and running-action guard (7) each report the expected number of tests and exit 0 in both modes. Otherwise FAIL and retain the first failure.

**C.** The suite uses deterministic test fixtures. This validates the directly affected CPU contract tests and does not measure how often the schedules occur in operation.

**U.** No Doom process, model, GUI, OS input, live threat, physical input release, task effect, or live allocation was used. This result does not satisfy Issue #59's live acceptance gate.

## Result

**PASS.** All four suites passed in normal and optimized Python: 15 + 20 + 9 + 7 = 51 tests per mode, 102 test executions total. The import-reachable overlay contains only the exact candidate sources needed by these suites; `RESULT.json` lists each source blob and SHA-256. Raw outputs and independent audit are retained here.

## Reproduction

```powershell
py -3.13 -B research/doom/v39_pr8643_current_affected_suite_a09_20261009/run_suites.py
py -3.13 -B research/doom/v39_pr8643_current_affected_suite_a09_20261009/audit.py
```
