# Post-run correction: A01 is non-admissible duplicate work

This package's frozen baseline/candidate/auditor outputs and all test transcripts are retained unchanged for transparency. **Do not count the A01 construction or its PASS labels as Issue #59 evidence and do not merge this package.**

After the one-shot CPU construction, a refreshed Issue #59 comment (5986729668) exposed the full related lineage: #5156 A04 already tested two same-key admissions followed by an ambiguous release (its formal audit STOP is consumed), and #7750 A03 already tested repeated same-key cycles with an independent audit and 12/12 identity/context/authority corruption controls. That correction explicitly withdrew the repeated-same-key discriminator and said not to rerun it. This A01 work therefore duplicated a prohibited/consumed question, despite using a changed consumer fixture. It adds no admissible scientific evidence.

The recorded PASS is only a property of the duplicate synthetic fixture and implementation; it is superseded for research disposition by `NON_ADMISSIBLE_DUPLICATE_PROTOCOL_DEVIATION`. The issue and draft PR are being corrected/closed. No baseline/candidate/audit retry or further repeated-same-key experiment is allowed.
