# Issue #5590 — Docker T2 Obstac output-mount successor

Fresh, additive successor to host-only T0 and the preserved Docker T1 output-mount STOP. T2 tested a writable-output probe under explicit runner UID/GID before candidate invocation. Candidate, ledger, auditor, and tests remain byte-identical to T1. The one-shot formal Docker allocation completed as `PASS_BOUNDS_SCOPED_DOCKER_REPRODUCTION`; see [REPORT.md](REPORT.md) and the exact artifact files in `results/docker-t2-01/`.

See [PLAN.md](PLAN.md), [FREEZE.json](FREEZE.json), and [SHA256SUMS.txt](SHA256SUMS.txt). Formal runtime artifacts, if produced, belong under `results/docker-t2-01/`.
