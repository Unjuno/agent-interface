# Recovery status for #2781 allocation 02

This recovery preserves the exact corrected pre-formal freeze. It does not
rewrite the predecessor allocation or claim a new result.

- Allocation 01 remains `STOP_EXTERNAL_EXECUTION_ENVELOPE / HOLD_FORMAL_INCOMPLETE`
  with its partial Inkscape/LibreOffice cases. Those rows are not pooled into
  allocation 02 and allocation 01 was not resumed.
- Allocation 02 was frozen before case 0 with denominator 16 and formal count
  0. No case was started by this recovery.
- The frozen execution environment records CPython 3.13.5. The available local
  X11/application image checked for this recovery provides CPython 3.12.14, so
  it is not the frozen interpreter. No formal substitute run was attempted.
- `PREFORMAL_SOURCE.tar.xz`, the correction patch, both freezes, schedule,
  source, scorer, controls and auditor are preserved unchanged. The patch can be
  checked/applied to the archived study source without invoking the study.

Disposition: `HOLD_NOT_RUN_ENVIRONMENT_MISMATCH`. Do not interpret this as a
scientific failure or as completion of #2781. Only a correctly reproduced frozen
environment may start the still-unconsumed allocation 02; retain the frozen
one-case stop-on-first-error rule.
