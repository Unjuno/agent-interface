# v39 session callback emission construction A01

This package tests one pre-live integration seam in PR #7355: the real v39 session `main()` invokes the release backend, its callback writes emitted rows to both runtime JSONL files, and its cleanup serializes owner history to `owner-events.json`.

The exact session and backend source files are pinned in `FREEZE.json`. `run.py` invokes the complete `session_map01_v12.main()` function with a fake X11 session, fake VizDoom module/game, fake Executor, and fake owner. It does not create an X server or issue OS input. Two saved construction captures retain one release row with a nested owner key-up receipt, byte-identical `events.jsonl` and `delivered.jsonl`, an explicit owner key-up record, and a verified-empty cleanup record. `audit.py` checks source SHA-256/Git blobs and both saved captures (24 checks).

Reproduce with a fresh output ID so retained evidence is never overwritten:

```sh
python -B research/doom/results/map01-v39-session-callback-emission-a01-20261004/run.py --run-id run-04
python -B research/doom/results/map01-v39-session-callback-emission-a01-20261004/audit.py
```

Existing run IDs intentionally fail closed if their output already exists. `SETUP_FAILURE_01.txt` preserves the initial import-wiring failure before `main()` ran; `raw/run-01-summary.json` preserves the first successful probe summary whose temporary logs were not retained. `RUN.md` distinguishes those from the two retained captures.

**Scope:** construction evidence for receipt serialization only. Fake owner/executor/X11/VizDoom; no X server, physical key state, real game, application feedback, task effect, recovery, latency, or live allocation. Issue #59 remains open.
