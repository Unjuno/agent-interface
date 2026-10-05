# V28 health-envelope counterfactual A01

This offline replay asks how the current-main V39 typed health guard would
classify the exact source-to-invalidation snapshots from five interrupted
planner turns in retained `map01-fixed-threat-v28-live-01` evidence. It sweeps
all supported `maximum_health_loss` values (0–20), fixes the critical health
minimum at 35 and source age at 30 seconds, and keeps the ammo hard floor at 1.

The candidate reads the retained report, event stream, manual frame review,
current V39 guard helpers and current typed guard. It writes only to a fresh
output path. The independent auditor does not import the candidate; it rebuilds
the five frame/event joins and recalculates all 105 health/ammo outcomes and
summary counts from the frozen source inputs. Three post-run black-box mutation
controls reject a changed source-span value, a changed guard floor in raw
output, and an omitted sweep row. They use temporary copies and leave the
frozen A01 output untouched; see [`AUDIT_CONTROLS.md`](AUDIT_CONTROLS.md).

## Result

The independently audited interruption counts for loss budgets 0 through 20
are `5, 5, 4, 3, 3, 3, 0, ... 0`. Thus, under the snapshot-only replay, budgets
0–1 hard-invalidate all five spans; 2 invalidates four; 3–5 invalidate three;
and 6–20 invalidate none. At budget 2, one two-point health change reaches the
inclusive floor and becomes `SOFT_CHANGED`. At budget 3, the three-point change
also reaches the inclusive floor. The one-point ammo change remains
`SOFT_CHANGED` at every health budget because ammo stays above its hard floor.

This curve is a mechanical result, not a recommendation that 6 health points
is safe. The original V28 invalidations came from a changed-pixel region guard;
the paired snapshots do not identify damage timing, intermediate state,
concurrent planner completion, or whether existing cover remained tactically
appropriate. This replay cannot satisfy Issue #59's integrated live evidence
requirements. The output can only inform a separately frozen prospective test.

## Reproduction

From the repository root, run the candidate once with a new output path, then
run the auditor with that raw file and a different new audit path:

```powershell
python research/doom/v28_health_envelope_counterfactual_a01_20261005/candidate.py research/doom/v28_health_envelope_counterfactual_a01_20261005/outputs/next/candidate-raw.json
python research/doom/v28_health_envelope_counterfactual_a01_20261005/audit.py research/doom/v28_health_envelope_counterfactual_a01_20261005/outputs/next/candidate-raw.json research/doom/v28_health_envelope_counterfactual_a01_20261005/outputs/next/audit.json
python -B -m unittest research.doom.v28_health_envelope_counterfactual_a01_20261005.test_audit -v
```

The checked-in `outputs/a01` directory contains the one frozen run. Raw source
hashes and the auditor's raw hash bind it to the exact inputs. Python 3.11.9 was
used on Windows. `wslc.exe` was unavailable. No Docker/Engine, network service,
game, model, GUI, X server, OS input, GPU, or live allocation was used.
