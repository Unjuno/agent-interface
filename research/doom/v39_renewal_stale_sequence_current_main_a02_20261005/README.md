# V39 stale-sequence renewal boundary — frozen-source A02

This additive construction revalidates the retained stale-renewal rejection against the frozen main snapshot `b6907899f11b036f2af572e8d4794ebb4b7e5c83`. It preserves the earlier A01 package unchanged. Exact controller and cleanup source snapshots are frozen in `FREEZE.json`.

`python run_checks.py` runs the source-extracted renewal boundary and actual `ControllerFailureCleanup` helper once in normal mode and once with `python -O`, then compiles the harness and source snapshots. `audit_currentmain_a02.py` independently checks the retained JSON, lifecycle order, no-live scope, process exits and exact source hashes. All outputs and audit repairs are retained in this directory; see `RESULT.md` for the scoped disposition.

Current-main applicability note: A02 is tied to frozen source `b6907899f11b036f2af572e8d4794ebb4b7e5c83`; see `CURRENT_MAIN_RECHECK.json`. Current main has advanced and this result is not asserted as a current-main finding.

