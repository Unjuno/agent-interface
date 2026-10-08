# V39 recovery post-merge current-main regression A10

## H / T / D / C / U

**H.** PR #8643's merged recovery changes should preserve the directly affected V39 controller, pending-observation, final-action admission, and running-action guard tests on the exact merge commit.

**T.** Freeze current main at merge commit `0a9e1b95520b2725ae5b4af51be87b472569f085` for PR #8643. Extract each selected test and its statically import-reachable Python sources from that commit into a temporary overlay. Run all four suites normally and with `-O`, retaining exact source identities and raw output.

**D.** PASS if all four suites report their frozen counts (15 + 20 + 9 + 7) and exit 0 in both modes. Otherwise FAIL with raw output retained.

**C.** The suite uses deterministic fixtures and validates integrated source after merge, beyond candidate-branch CI. It does not measure how often the schedules occur in a live game.

**U.** No Doom process, model, GUI, OS input, live threat, physical input release, task effect, or live allocation was used. This does not satisfy Issue #59's live acceptance gate.

## Result

**PASS.** The merged-main overlay passed all four suites in both normal and optimized Python: 15 + 20 + 9 + 7 = 51 tests per mode, 102 total test executions. The independent audit verified every source blob and SHA-256 against merge commit `0a9e1b9`. Issue #59 remains open and unassigned; the live gate is still outstanding.

## Reproduction

```powershell
py -3.13 -B research/doom/v39_recovery_postmerge_main_a10_20261009/run_suites.py
py -3.13 -B research/doom/v39_recovery_postmerge_main_a10_20261009/audit.py
```
