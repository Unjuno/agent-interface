# Issue #3711 downstream-truncation evidence

- [Allocation 01 STOP](formal-01/STOP.md) — preserved; never retried.
- [Construction import checks](preflight/CONSTRUCTION.md) — two source-closure STOPs, then import-only PASS.
- [Successor allocation 02 freeze](successor-02/PLAN.md) and [hash manifest](successor-02/FREEZE.json).
- [Formal-02 result](formal-02/REPORT.md), raw artifacts, and [container run record](formal-02/CONTAINER_RUN.md).
- [Reproduction guide](RUNBOOK.md).

Allocation 02 is a scoped synthetic pass for downstream JSON rejection plus read-only retained-result recovery. It is not evidence that arbitrary CLI callers handle process exit code 0 safely; see the report's limitation.
