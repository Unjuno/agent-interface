# Issue #6505 — independent audit-only successor A01

This package independently audits the exact retained raw evidence from #4889 without executing its original candidate, reducer, or auditor. It preserves the original `HOLD_AUDIT_CONTROL_HARNESS` and the no-op `linearizations` control unchanged.

Start with [PREREGISTRATION.md](PREREGISTRATION.md), then [REPORT.md](REPORT.md) after the one-shot audit. The original archive remains at `research/analysis/partial_order_replay_4889_v1/evidence/`; `auditor.py` reconstructs and verifies it from the frozen base tree rather than duplicating 3.2 MB of raw data.

This is only an audit of a finite authored reducer result. It is not evidence about real traces, GUI/runtime replay safety, storage savings, latency, or product behavior.
