# Commands and execution record

All work was local in the candidate worktree, not a GitHub Actions/workflow run.

## Preflight

```sh
python -B -m unittest -v test_probe
python -B -m py_compile probe.py audit.py test_probe.py
```

The tests ran from this bundle directory in Arch WSL and in local Docker with `python:3.13-slim-bookworm`; both suites passed 5/5. Docker was used for fast CPU-only iteration. The actual host probe remained in Arch WSL because it measures that host's WSLg socket metadata.

## One-shot construction probe

```sh
python -B research/x11/issue5243-private-xvfb-terminate-reset-20260930/probe.py \
  research/x11/issue5243-private-xvfb-terminate-reset-20260930/results/construction-01
```

Executed once from the repository worktree in Arch WSL. Exit code 0. Raw wrapper, child, and Xvfb log are retained under `results/construction-01/`.

## Auditor

The first launch attempt used an invalid relative path. Its stderr/empty stdout/status are retained as `audit-launch.*`. The path was corrected without changing frozen code or probe output, then the auditor was executed once:

```sh
python -B ../../audit.py result.json >audit.stdout 2>audit.stderr
```

Auditor stdout is retained verbatim and reports PASS with 12 checks and six rejected corruption controls. Stderr is empty. The shell's status-capture artifact `audit.exitcode` is empty; see `REPORT.md` for this provenance limitation.
