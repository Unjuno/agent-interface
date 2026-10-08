# Issue #4144 recovery status — partial-source archive with raw HOLD

Disposition: `HOLD_FULL_RAW_PUBLICATION`. This recovery preserves the exact
13-file package present on the canonical remote branch
`research/referenced-image-gc-concurrency-20260922` at
`615d059bc9036a93979858397debd9f2307f8abb`. It does not complete or
independently validate the reported 24-case formal result.

## What is present

Frozen plan/environment/source, the readable report/result, evidence manifest,
publication HOLD, and the original evidence unpacker are retained unchanged.
The manifest declares six ordered base64 parts for a 24,820-byte archive with
SHA-256
`d9acde085250d0c868f319846bb06dd83fc7f5271fc83d623608a7908f044216`.

## What is missing

All six declared evidence parts (`evidence_part01.b64` through
`evidence_part06.b64`) are absent from the branch tree. Consequently the
archive, 24 formal raw rows, process/actor receipts, and raw-only audit inputs
cannot be reconstructed from this checkout. `RESULT.json` and `REPORT.md`
retain the Issue-reported PASS, but that result remains historical and
unverified from repository-retained raw bytes.

## Checks and limits

- All six available Python files syntax-compiled; all four JSON files parse.
- The full audit/control suite was not run because its required raw evidence
  parts are missing. This is a publication STOP, not a scientific FAIL.
- Formal rerun, raw re-audit, and corruption-control replay by this recovery:
  **0**. No bytes were reconstructed or inferred.

This may be merged only as a partial archival/status record, not as a complete
reproducibility bundle or runtime promotion. Keep Issue #4144 open until the
exact six original evidence parts are recovered, hash-verified, restored, and
audited.
