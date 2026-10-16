# A07 saved-trace audit-v3 addendum

This is an additive read-only reconciliation of the retained A07 episode. It
does not replace `AUDIT.json`, `AUDIT_V2.json`, or the preregistered HOLD.

## Inputs and custody

- Source auditor: `audit_live_v3.py` from PR source commit
  `6e308de606ef684ee07406b40958c3275c0bc7aa`, SHA-256
  `8784e0e2cbf4148aeb88562a200ff8979324b749dceaf6a73d7e27524fbcc09e`.
- Local ignored A07 output manifest: 2,358 entries, all byte counts and hashes
  matched; manifest SHA-256
  `a7ed0abe21ad1571131511abfb1b248a61ed5d13e7eaafd196caf2a741ef5844`.
- The auditor ran against temporary copies of `AUDIT.json`, `AUDIT_V2.json`,
  `episode/report.json`, `episode/runtime/events.jsonl`, and
  `episode/runtime/score.json`. The output below was saved separately; the
  original ignored output directory and its audits were not written.

## Result

`A07_SAVED_TRACE_AUDIT_V3.json` records `status=FAIL`, `scoped_pass=false`, and
`formal_pass=false`. There are 10 unique, matched cancellation IDs and no
post-cancel admissions. Four cancellations have no input admission or release
transition. Six have admissions: `cover-1`, `cover-2`, `cover-3`, `cover-4`,
`cover-5`, and `cover-8`. Five of those six have one fewer release-transition
row than admission rows (three are 6/5 and two are 4/3); `cover-3` is 4/4.
The five unmatched per-key counts make v3's custody check fail.

The corresponding `input_released.owner_release` receipts report empty key
state. That alone does not resolve whether each `input_admission` represents a
key-down already sent or a command admitted but cancelled before sending. The
saved owner-event trace must be reconciled to distinguish those cases. Until
then, the v2 custody PASS is not independently confirmed by v3, and the v3
scoped FAIL is not evidence of a physical stuck key. Keep A07's overall result
at HOLD; do not rerun the allocation.
