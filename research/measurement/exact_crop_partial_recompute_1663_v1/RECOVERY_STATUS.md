# Issue #4083 recovery status — source preservation only

Disposition: `HOLD_EVIDENCE_PUBLICATION_INCOMPLETE`. This recovery preserves
the exact branch-only package as it exists on
`research/exact-crop-partial-recompute-1663-20260922` at
`f224e582c19d3c17ac1b09b6ae9699950baa12db`. The original 25 files are copied
without edits; the original historical branch remains intact.

## What is available

- Frozen plan, construction and allocation metadata, candidate and study code,
  tests, a report, and the compact `AUDIT_V2.json` summary.
- The branch's capsule fragment `capsule/evidence.b64.part00` (8,000 bytes)
  and audit-v2 publication fragments are retained exactly as found. Their
  presence does not mean either archive is complete or reconstructible.
- The two upstream source blobs required by the freeze are present in canonical
  main paths with the expected Git blob IDs. This recovery does not duplicate
  or modify those upstream files.

## What is not verified

Issue #4083 reports a 9-case / 216-request allocation-03 contract and cost
PASS, but the declared complete raw capsule (47,164 bytes; SHA-256
`aa5be683d71aaf3ee7d4931bcf101257d914b9ef2a09ad5e817fc6c26bd2df43`; expected
Git blob `70cbcb361913776269e364567e6ea780a80f6803`) is not present. The
available capsule fragment is incomplete; the Issue records a postformal
audit-v2 transfer mismatch. The full raw rows, child/batch receipts, and
reproducible audit-v2 implementation/output package therefore have not been
independently re-audited from this repository snapshot. The Issue-reported
PASS and timing ratios remain historical reports, not a result validated by
this recovery PR.

## Checks and boundary

- `audit.py`, `candidate.py`, `study.py`, and `test_study.py` syntax-compiled.
- The six construction/unit tests passed in a disposable macOS arm64 / CPython
  3.13.14 environment with NumPy 2.3.5 and Pillow 12.3.0; exact upstream
  sources were read from their canonical main paths. These checks do not
  recreate the frozen Linux CPython 3.13.5 formal environment.
- Formal allocation, timing, raw audit, and corruption replays performed by
  this recovery: **0**. No missing bytes were synthesized and no runtime code
  or production claim is introduced.

This is an archive/source recovery with publication HOLD, not a promotion of
the reported scientific result. Keep the original branch and Issue open until
the exact original raw/source capsule is recovered and its hashes and audit
receipts can be read back.
