# Prior-table reconciliation supplement

This additive directory closes the retained cross-document reconciliation gap identified during review of Issue #6198 / PR #6203. Start with `RECONCILIATION_PLAN.md` for H/T/D/C/U and frozen acceptance criteria, then `SUPPLEMENT_REPORT.md` and `SUPPLEMENT_RUN.json` for the formal outcome. `RECONCILIATION_FREEZE.json` pins source and inputs; `RECONCILIATION.json` is the one-run machine result; `AUDITED_INTERVALS.json` is the byte-identical #6175 table transcription; `reconcile.py` and `test_reconcile.py` provide the isolated comparator and synthetic tests. `SHA256SUMS` records this supplement's files except itself.

The comparator only compares already-retained files. It does not invoke the candidates or the original #6198 auditor and cannot independently authenticate #6175's absent original receipts.
