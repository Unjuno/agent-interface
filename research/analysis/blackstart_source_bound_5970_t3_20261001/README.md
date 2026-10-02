# Issue #5970 T3 — source-bound prospective trace

This rung mechanically derives instrumented executables from the exact archived #4135 `app.py` and `observer.py`. See `PLAN.md` for H/T/D/C/U; `FREEZE.json` identifies the archive and source; `FREEZE_T3.json` freezes this candidate, independent auditor, transformation, construction tests, and derived diff before the one-shot run. `REPORT.md` and `RUN.md` retain the disposition and exact attempt ledger. T0/T1/T2 remain unchanged.

The T2 observer-event HOLD is not treated as evidence against original #4135: T3 tests only a deterministic additive source transformation. The WSL2/Xvfb fallback is isolated from the desktop; Docker Desktop's Linux engine was not usable at start-gate time.
