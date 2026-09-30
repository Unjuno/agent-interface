# Issue #5590 — Docker T2 Obstac output-mount successor

Fresh, additive successor to host-only T0 and the preserved Docker T1 output-mount STOP. T2 is designed to test a writable-output probe under explicit runner UID/GID before candidate invocation. Candidate, ledger, auditor, and tests remain byte-identical to T1. No formal candidate result exists until the one-shot allocation runs and the independent raw-only auditor passes.

See [PLAN.md](PLAN.md), [FREEZE.json](FREEZE.json), and [SHA256SUMS.txt](SHA256SUMS.txt). Formal runtime artifacts, if produced, belong under `results/docker-t2-01/`.
