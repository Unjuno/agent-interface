# Run record

- Base: `3f24e85bff32a93fbc1ca244f7f249b843710743`.
- Candidate baseline: PR #7829 head `70c76483c46108bdd70bf2fb90679d948a5f156f`.
- Command: `python -m unittest research.doom.map01_v39_production_release_barrier_a04_20261005.test_production_release_barrier -v`.
- Runtime: host Python 3.14.5; 3 tests passed. Full raw output is `PRODUCTION_BARRIER_RAW.log` and the independent raw-only audit is `INDEPENDENT_AUDIT.json` (`audit.py`).
- Preserved failing control: same treatment without the candidate `release_all` drain; one test fails because it observes zero release-measurement rows before terminal. See `NO_FLUSH_CONTROL_RAW.log`.
- Container gate: STOP; no container run was completed. Exact daemon error is recorded in `CONTAINER_STOP.txt`.
- Interpretation: synthetic harness boundary only. No real X11, game, task effect, or Issue #59 live exit-gate claim.
