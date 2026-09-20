# Issue #3814 formal allocation issue3814-jsonl-frame-01

## Decision

`STOP_SETUP` — the sole frozen runner invocation stopped during Python module import, before constructing any experiment row. The failure was a launch-command omission: `PYTHONPATH=/source` was not supplied to the container. The frozen runner imports `runtime.cli_v1` from the read-only source mount and therefore could not resolve `runtime` from its own experiment directory.

No synthetic dispatch facade ran. No attempt directory was reserved; `attempt-status` and `review` were not invoked; no raw evidence was written; no independent evidence-audit container was started. This is not a finding about parser-only completion, newline framing, recovery, or replay.

The one-allocation/no-retry preregistration was honored after this setup failure. The frozen `PLAN.md`, `runner.py`, and `audit.py` were not changed. A corrected, distinct allocation is tracked in [Issue #3840](https://github.com/Unjuno/agent-interface/issues/3840); it must set `PYTHONPATH=/source` and bind a separate immutable runner/plan before execution.

## Scope

This records only the setup failure for allocation `issue3814-jsonl-frame-01` on Docker Desktop 28.5.1, Linux/amd64, using the pinned `python@sha256:44ff437bba879d4941b710a369a8f19266aea34b29002807f0c487fabc9eec9b` image with network disabled and read-only source. It provides no experimental outcome and does not close #3814's underlying research question.
