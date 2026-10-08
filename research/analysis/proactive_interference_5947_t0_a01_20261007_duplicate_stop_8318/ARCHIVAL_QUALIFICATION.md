# Archival qualification

This directory is an isolated custody archive of the later duplicate execution in draft PR #8318. It is not a scientific successor and does not alter predecessor PR #8317's first-run `HOLD_AUDITOR_COVERAGE`.

- Original branch: `research/5947-matched-context-t0-a01-20261007`
- Original head: `50aa691d877e5fb4bfd0a5c4c49e537e21f540eb`
- Original recorded base/allocation: `798ac5ad709168ff1d27b115f10f4f96b126bb71` / `5947-MULTI-UPDATE-PROVENANCE-T0-A01-20261007`
- All 13 original package files are retained under this separate `_duplicate_stop_8318` path. Candidate/auditor raw outputs remain distinct from #8317 and are not combined with them.
- `FREEZE.json`, `SHA256SUMS.txt`, and `RUN_RECORD.json` remain byte-identical to the source branch. SHA256SUMS uses the predecessor path as its historical label; map that prefix to this directory when verifying each retained file.
- The execution is `STOP_DUPLICATE_ALLOCATION_ALREADY_CONSUMED`, not a valid allocation-level PASS. No formal rerun, repair, or scientific claim is made here.

Construction tests call the candidate/auditor logic and are therefore not rerun during this custody-only rescue. CI may perform repository-level index checks; no experimental entrypoint is authorized.
