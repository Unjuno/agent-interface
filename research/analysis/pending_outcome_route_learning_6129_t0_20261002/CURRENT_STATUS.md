# Issue #6129 allocation index

This file is the current summary; allocation artifacts below are immutable.

- [T0-01](REPORT.md): five-case pending-bounds card, `PASS_METHOD_SCOPED` within its initial narrow fixture; not the complete Issue T0.
- [T0-02](T0-02/REPORT.md): typed endpoints, intermediate YIELD and switch-cost accounting, `PASS_METHOD_SCOPED`; explicitly records its remaining inversion-reconstruction gap.
- [T0-03](T0-03/REPORT.md): explicit eight-attempt delayed ranking inversion plus null, censoring, typed terminal, recovery, cross-task mismatch, no-lookahead and switching-cost controls; `PASS_METHOD_SCOPED`, 7/7 cases, local tests 9/9, checksums pass.

Together T0-03 supplies the missing finite method checks identified in the Issue discussion. This is not empirical route evidence. Keep Issue #6129 open for possible T1 only if a separately authorized workload meets all source-bound attempt/effect attribution, censor-reason, task-mix and independent-oracle gates. Otherwise retain `HOLD_NO_IDENTIFIABLE_FEEDBACK`; no live route or production change follows from these synthetic results.
