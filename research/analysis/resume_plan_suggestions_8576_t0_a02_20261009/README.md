# Issue #8576 T0 A02 — executed mutation-gate requalification

A02 is an append-only successor to A01. It leaves A01's frozen files and one-shot outputs untouched and addresses the specific qualification that A01's auditor hardcoded `mutation_controls_rejected: 6` without running those controls. A02's auditor now constructs six named mutations, routes every copy through its independent reconstruction validator, and records each actual rejection and reason.

The synthetic 12-case candidate scope remains method-only. No participant, real user data, GUI, model, continuation action, human-benefit claim, or product claim is included. Formal result and limits are reported in [REPORT.md](REPORT.md) after the frozen single execution.
