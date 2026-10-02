# STOP — r3 construction invocation

Allocation: `issue2476-track-cumulative-drift-evidence-construction-r3-20260928`

## Outcome

`STOP_OPERATOR_INVOCATION_ERROR_NO_RETRY`.

The frozen Docker runner was invoked once, locally, against the pinned image. The command supplied `--output /source/raw-run/raw.json`, but the frozen CLI requires `--source SOURCE --out OUT`. It exited with status 2 at argparse usage validation before constructing rows. There is no `raw.json`; no trajectory row was produced and the separate auditor was not run because there is no runner artifact to audit. The allocation's no-retry rule prohibits correcting the command and invoking it again.

This is an operator invocation error, not evidence for or against H. The only valid conclusion is that r3 yielded no construction result. The four frozen auditor unit tests passed before the runner invocation; that does not substitute for the planned construction or audit.

## Invocation and retained evidence

The attempted command used the frozen image `python:3.13.5-slim-bookworm`, image ID `sha256:4c2cf9917bd1cbacc5e9b07320025bdb7cdf2df7b0ceaccb55e9dd7e30987419`, `linux/amd64`, network disabled, read-only root and source, 1 CPU, 256 MiB memory/swap, 32 PID limit, dropped capabilities, and no-new-privileges. The attempted CLI tail was `-B run.py --output /source/raw-run/raw.json`.

Captured stderr/stdout:

```text
usage: run.py [-h] --source SOURCE --out OUT
run.py: error: the following arguments are required: --source, --out
```

Exit status: `2`.

Captured files: `raw-run/stdout.txt`, `raw-run/exit_code.txt`. `raw-run/raw.json` is absent. Docker daemon reports version `29.8.0`, Linux/x86_64. No formal #2476 matcher/task trajectory was run; formal invocation count remains zero.

## Source integrity

The five frozen source SHA-256 values were rechecked after the stop and remain byte-identical to `FREEZE.json` and the previously verified Git blobs. No source, fixture, decision threshold, or prior allocation was changed. No retry, replacement run, or post-result tuning occurred.

The recorded stdout file SHA-256 is `5073660adbc2741019a8dc45acb9578b09998fea0d6e800667e0aa587a5576f9`; exit-code file SHA-256 is `d4735e3a265e16eee03f59718b9b5d03019c07d8b6c51f90da3a666eec13ab35`.

## Scope

This STOP says nothing about visual tracking, physical input, task effect, matcher performance, or the validity of the 12 px bound. It is preserved as the first outcome for this immutable construction allocation.

