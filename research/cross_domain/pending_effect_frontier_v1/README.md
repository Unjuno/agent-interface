# Pending-effect frontier: isolated research candidate

See `REPORT.md` for the 75-case result and its limits, `FROZEN_PLAN.json` for the pre-execution GitHub receipt, and `results/summary.json` / `results/cases.csv` for machine-readable retained results.

- `frontier.py`: read/write-conflict scheduling advice and exact commit-receipt matching; grants no input authority.
- `fixture.py`, `experiment.py`, `private_desktop.py`: native Tk/XTEST controlled experiment; not production runtime integration.
- `audit.py`, `replay.py`: independent database/log replay.
- `test_frontier.py`: 30 deterministic tests including 4,096 effect pairs.
- `test_audit.py`: 9 mutation tests requiring the development fixture in the full evidence bundle.

GitHub retains exact source bytes, prefreeze receipt, report, compact per-case results and full-bundle digest. The full raw bundle (75 databases and traces) is delivered in the originating conversation; it is not claimed to be uploaded to GitHub. `archive.json` states its location and hash. Extract that bundle before running full replay. No workflow, shared runtime, existing result or historical preregistration is changed.

**Do not rerun consumed allocation IDs. Do not interpret 75 expected-outcome audits as 75 exact task successes. No general speed, model or Doom efficacy claim.**
