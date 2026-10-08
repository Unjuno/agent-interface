# V39 current-main affected-suite regression A11

## H / T / D / C / U

**H.** The current `main` controller and pending-observation changes after the PR #8643 merge preserve the directly affected V39 and action-guard CPU contract tests.

**T.** Freeze exact GitHub `main` commit `a6343bb76e4dc0a4afa32a29c8a485a617faeff8`. Extract four existing test suites and their statically import-reachable Python source from that commit into a temporary overlay. Run normally and under Python optimization; retain source blob/SHA-256 identities, raw stdout/stderr, and exit receipts.

**D.** PASS only if controller (15), pending-observation drain (20), final-action admission (9), and running-action guard (7) all report the frozen counts and exit 0 in both modes; otherwise retain first failure as FAIL.

**C.** These are deterministic CPU fixtures. Source change review shows the controller and pending-drain test modules changed after A10's source commit; runtime frequency is not measured.

**U.** No Doom process, model, GUI, OS input, live threat, physical key release, task effect, or live allocation. This cannot satisfy Issue #59's live gate.

## Reproduction

```powershell
py -3.13 -B research/doom/v39_recovery_current_main_a11_20261009/run_suites.py
py -3.13 -B research/doom/v39_recovery_current_main_a11_20261009/audit.py
```
