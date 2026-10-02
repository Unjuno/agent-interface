# Recovery status — Issue #2476 construction r3

Exact-content archive of the nine files from remote branch
`research/doom/track-drift-2476-r3-20260928`, source tip
`6e900544a734cb31dbb96de53584e9daf7ea2970`. The original files are unchanged.

The frozen one-shot local Docker invocation stopped with
`STOP_OPERATOR_INVOCATION_ERROR_NO_RETRY`: the supplied `--output` option did
not match the runner's required `--source/--out` CLI. Argument parsing exited 2
before any construction rows; no raw result was created and the auditor did
not run. Issue #2476 explicitly prohibits retrying this consumed allocation.
This is an operator invocation STOP, not evidence for or against the track-drift
hypothesis and not a formal matcher/game result.

Recovery performed no Docker run, auditor execution, GUI/game call, or input.
