# #6198 T1 replay package

This package preserves the newly executed replay receipts for Issue #6198. Start with `REPORT.md`; `PLAN.md` freezes the question and decision boundary, `FREEZE.json` binds source and inputs, `candidate_v38.json` / `candidate_v39.json` retain the exact analyzer outputs, and `audit_raw.py` / `audit.json` retain the independent raw-only reconstruction.

Run details and environment are in `RUN.json`. `SHA256SUMS` covers every package file except itself. This is a host-CPU historical receipt replay only, not new live/MAP01 data or a physical key-state measurement.
