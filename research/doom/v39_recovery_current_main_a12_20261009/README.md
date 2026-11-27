# V39 current-main affected-suite regression A12

## H / T / D / C / U

**H.** The current `main` V39 controller and pending-observation changes preserve their affected CPU contract suites after the current test counts are independently read from the exact source.

**T.** Freeze source commit `a6343bb76e4dc0a4afa32a29c8a485a617faeff8` and suite counts 16 + 22 + 9 + 7. Extract the selected tests and their static import closure from that commit into a temporary overlay; execute normal and optimized Python 3.13.14 and retain all source identities and raw outputs. A11's initial stale-count gate failure remains at its own path.

**D.** PASS only if each suite reports its frozen count and exits 0 in both modes; otherwise retain failure.

**C.** Deterministic CPU contract tests only. They do not estimate schedule frequency or establish live behavior.

**U.** No Doom process, model, GUI, OS input, threat exposure, physical release, task effect, or live allocation. This cannot satisfy #59's live gate.

## Reproduction

```powershell
py -3.13 -B research/doom/v39_recovery_current_main_a12_20261009/run_suites.py
py -3.13 -B research/doom/v39_recovery_current_main_a12_20261009/audit.py
```

A11 preserves the initial copied-gate failure and disposition separately.

At publication, `main` advanced to `57337e95ecbecf7e762c8ec8091472b79e8ad49f`. `verify_main_carry_forward.py` checks each of the 34 pinned source blobs against that tip and confirms no changed main path overlaps the source closure; it does not rerun the suites.
