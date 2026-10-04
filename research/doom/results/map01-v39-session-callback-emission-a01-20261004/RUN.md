# Run record

- Base: PR #7355 exact head `6ed0235da58ad849fc07daf75ce49a88ad46d407`.
- Candidate: `python -B research/doom/results/map01-v39-session-callback-emission-a01-20261004/run.py --run-id run-03` (run-02 used the equivalent initial harness path).
- Candidate process exit: 0 (the complete `session_map01_v12.main()` call returned and post-run assertions passed).
- Captured session stream: `raw/run-02-stdout.txt`.
- Persisted runtime records: `raw/run-02/events.jsonl`, `raw/run-02/delivered.jsonl`, `raw/run-02/owner-events.json`, and `raw/run-02/score.json`.
- Independent audit: `python -B research/doom/results/map01-v39-session-callback-emission-a01-20261004/audit.py` — 24/24 checks passed.
- Adjacent regression tests on the same checkout: backend and session cleanup suites 23/23; Python compilation and `git diff --check` passed.

The first successful probe is retained only as `raw/run-01-summary.json` because its runtime directory was temporary. `run-02` and `run-03` are retained captures of the same construction probe; run-03 exercises the portable runner. The published `run.py` accepts a new run ID and refuses to overwrite any existing output directory. They are not independent replications and not formal/live allocations. `SETUP_FAILURE_01.txt` preserves the earlier harness-only import error before `main()` ran.

Scope remains fake X11/VizDoom/executor/owner. No X server, OS input, physical key state, application feedback, model, latency, recovery, or task effect was observed.
