# Run record

Environment: CPython 3.12.14, macOS arm64, Pillow 12.3.0. Host-only; no container or isolation enforcement is claimed. The previous OrbStack image-inventory failure was not retried for this in-memory source-contract test.

The frozen command set in `FREEZE.json` is executed once each from this package directory as `python -B run_probe.py` and `python -B audit.py`. In this worktree the calls used the bundled interpreter by absolute path from the repository root; their stdout/stderr are redirected to the retained files: `candidate.stdout`, `candidate.stderr`, `candidate.exit`, `auditor.stdout`, `auditor.stderr`, and `auditor.exit`. Both returned exit 0.

The runner command was `/Users/taka/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -B research/doom/v39_typed_epoch_alias_59_a01_20261005/run_probe.py`; the independent auditor command was the same interpreter with `.../audit.py`. The independent audit inputs are pinned in `AUDIT_FREEZE.json`.
