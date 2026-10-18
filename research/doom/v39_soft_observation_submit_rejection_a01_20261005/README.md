# V39 soft-observation submit-rejection recovery A01

H/T/D/C/U and frozen source identity: [FREEZE.md](FREEZE.md). Result and scope: [RESULT.md](RESULT.md).

The retained baseline RED shows a valid soft observation advancing the source sequence while an initial cover submit is pending; the controller then aborted on the expected stale-sequence rejection. The candidate records a no-admission decision from the fresh observation, with no planner start or cancellation of an unadmitted program.

Reproduce the focused candidate checks from the repository root:

```powershell
python -m unittest research.doom.test_overlap_controller_v39_wait -v
python -O -m unittest research.doom.test_overlap_controller_v39_wait -v
```

See the `*.stdout.txt` files for retained first output. `audit.py` is read-only and does not rerun the tests.
