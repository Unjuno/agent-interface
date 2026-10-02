# Issue #4195 recovery status — partial evidence archive with HOLD

Disposition: `HOLD_EVIDENCE_PARTS_MISSING_AT_CURRENT_HEAD`. This preserves the
exact 23 files on the canonical remote branch
`research/effect-owner-deadline-4186-20260923` at
`80fc4105721cfe2d471933e82638c7040382fa10`. No scientific result is changed
or promoted by this recovery.

## What is present

- Frozen plans/schedules, source and audit programs, readable result summary,
  publication metadata, and separate ID001 stop records.
- `STOP_EVIDENCE.tar.xz.b64` decodes to an 8,016-byte XZ archive with SHA-256
  `98bcc3d607626f72322470f308aeb72e46df6b484c0249d5a3375d7bb4da2f28`; the
  XZ integrity check passes and its member names were listed without
  extraction. This archive records the distinct incomplete ID001 allocation,
  not the missing ID002 36-case raw bundle.
- A metadata inconsistency is retained, not repaired: the encoded STOP
  evidence is 10,828 bytes with SHA-256
  `90feca992da7bdd32f2e1b4adb78db361704f87cb8b5a52ceb8f3b858af798a3`, while
  `STOP_EVIDENCE_MANIFEST.json` declares 10,829 bytes and a different hash.
  The decoded XZ bytes do match the manifest's declared XZ SHA-256.

## What remains unavailable

`PUBLICATION.json` declares four ordered ID002 evidence parts; all four are
absent at the original branch head. The Issue reports that the complete raw
capsule is not retrievable and binds it to SHA-256
`9c1a4d0dd991628e5ffa5258a51f19da2e0aaa62e2007a4bc1b60cff865a005b`. The
readable `RESULT_SUMMARY.json` and PR prose are not substitutes for those
raw rows, process/effect receipts, or the complete independent audit input.
The reported ID002 36/36 `PASS_EFFECT_OWNER_DEADLINE_SCOPED` therefore remains
historical and is not independently verified by this recovery.

## Checks and limits

- The nine available Python files syntax-compiled; all nine available JSON
  files parse.
- The separate ID001 STOP archive decoded to its declared XZ hash and passed
  `xz -t`; it was listed but not extracted or scientifically re-audited.
- Formal rerun, ID002 raw audit, and ID002 corruption-control replay: **0**.
  No missing evidence was reconstructed or inferred from the summary.

This is eligible only as a partial archival/status record, not as a complete
reproducibility bundle or runtime promotion. Keep Issue #4195 open for exact
ID002 evidence recovery. Preserve both allocation outcomes and the missing
parts boundary in any later successor work.
