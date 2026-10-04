# Issue #7411 T0 A01 — user-worthwhile benefit estimator

This host-only synthetic method test is `HOLD_AUDIT_INCOMPLETE`. The frozen candidate/auditor produced a nominal pass and recovered the planted medians within one 2-second dose, but post-run review found the auditor did not fully implement the preregistered raw-record and mutation checks. Its first outcome is preserved without retry.

Read [REPORT.md](REPORT.md) for the result and scope, [PROTOCOL.md](PROTOCOL.md) for the frozen test, [FREEZE.json](FREEZE.json) for input hashes, and [RUN.json](RUN.json) for executed commands and runtime classification. Raw synthetic choices, candidate output, independent reconstruction, and captured stdout are in `formal_01/`. Reproduce only the source audit with `python3 -B research/analysis/user_worthwhile_benefit_7411_t0_a01_20261004/audit.py`; do not rerun the frozen candidate allocation.
