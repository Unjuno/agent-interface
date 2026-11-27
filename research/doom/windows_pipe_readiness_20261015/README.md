# Windows anonymous-pipe readiness validation

PR [#8834](https://github.com/Unjuno/agent-interface/pull/8834) was held because
its Windows implementation had only been tested on macOS. This packet records
the missing Windows checks using local anonymous pipes. No GUI, game, display,
input injection, model, WSL or live allocation was used.

Baseline main `0ddd716a3e2c07d7dad54c8fc81fb21aa5ee67d6` ran 12 tests with one
error: its `select()` call cannot wait on this Windows anonymous pipe
(`WinError 10093`). Candidate `67905decc40a468b9dfe45ecfbcc8a6b83999689` replaces
that Windows branch with `PeekNamedPipe`, retaining POSIX `select()`.

The original 13 candidate tests passed. Four further tests cover empty-pipe
timeout and immediate data, buffered data followed by EOF, invalid descriptors,
and construction on one thread with all callbacks on the thread invoking
`run()`. All **17 tests passed normally and with optimized Python** on Windows
10.0.26300 / Python 3.13.14. Three dependent adapter/service/telemetry suites
also passed (11 tests) with fake game/session objects.

`VALIDATION.json` records conditions, LF-normalized source hashes and exact raw
log hashes. `baseline-normal.log` retains the failure; the two candidate logs
retain individual results. These are construction/transport results, not
MAP01, live task, release, recovery, efficiency or hard latency qualification.
The polling primitive's callbacks run synchronously; `PeekNamedPipe` in other
concurrent-reader arrangements is not proven bounded by these checks.

Reproduce the candidate tests from `research/doom`:

```text
python -B -m unittest -v test_main_thread_scorer_polling_v1
python -B -O -m unittest -v test_main_thread_scorer_polling_v1
```

The baseline can be reconstructed from the named main commit's two polling
module/test blobs. Saved logs are immutable evidence, not a request to rerun a
consumed live experiment. Source changes require fresh local validation.
