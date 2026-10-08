# Issue #3619 — first proxy effect-binding unit, formal-02

Successor allocation after #3610's startup STOP. See `PREREGISTRATION.md`, `FREEZE.json`, and `SOURCE_MANIFEST.json`. The formal launcher checks all bindings and tests before the single runner invocation; it uses `set -euo pipefail` so a preflight failure cannot fall through to formal execution.

Raw row data, independent audit, and `REPORT.md` are retained under `evidence/formal-02/`. Formal-02 is `HOLD_EVIDENCE_INCOMPLETE`: the intended ambiguous-target control appeared only after dispatch, and the independent release observer was miscalled. These failures are preserved; no formal retry was performed. The result is bounded to a disposable synthetic GTK/Xvfb counter task and is not a usability, model, latency, or production claim.
