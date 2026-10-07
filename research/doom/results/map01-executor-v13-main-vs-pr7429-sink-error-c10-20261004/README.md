# C10 — current-main executor v13 versus the #7429 sink-error fix

Question: does a filename-level selection of `executor_v13` on current `main` preserve the publication-failure contract in the latest #7429 source?

The current-main source and the #7429 branch define different implementations at the same `research/live_control/executor_v13.py` path. The latest #7429 regression suite was run against both closures, with current-main support modules held fixed. The current-main implementation passed 3/4 tests, but its release-event sink-error case raised an uncaught watcher exception and the terminal record lacked `input_release_publication`. The exact #7429 v12/v13 sources passed 4/4.

This narrows the earlier C09 result: source composition passes when the #7429 executor modules are explicitly overlaid, but a current-main checkout cannot select that implementation by the bare `executor_v13` import until the file-level conflict is reconciled. It is a source-level integration finding only.

Reproduce both saved runs from this worktree root:

```powershell
$env:PYTHONPATH = 'research/doom/results/map01-executor-v13-main-vs-pr7429-sink-error-c10-20261004/FROZEN/common-support'
python -B research/doom/results/map01-executor-v13-main-vs-pr7429-sink-error-c10-20261004/test_executor_v13_against_main.py -v
python -B research/doom/results/map01-executor-v13-main-vs-pr7429-sink-error-c10-20261004/FROZEN/pr7429/test_executor_v13.py -v
```

Both commands load the source closure archived below `FROZEN/`; the first test has only its import path redirected to `FROZEN/main`. The first command is expected to retain its single regression failure; the second is expected to pass. `audit_c10.py` checks both captured outputs, exit receipts and frozen source hashes. No game, X11, model, OS input, container, or formal allocation was used. This does not satisfy the current #59 evidence gate.
