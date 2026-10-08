# Archival qualification — Issue #5385 T1

This document qualifies the preserved preformal STOP packet. It does not
repair, replace, or reinterpret any original freeze, manifest, STOP record,
construction output, or source file.

## Disposition

`STOP_BEFORE_START_MAIN_DRIFT_AND_FREEZE_PROVENANCE`. The allocation was
relinquished before invocation. Candidate, formal auditor, and Docker
invocation counts are zero; retries are zero; the hypothesis is
`NOT_EVALUATED`. The later `STOP_CORRECTION.json` supersedes only the incorrect
time-window explanation in `STOP.json`: the scheduled window had not yet
started. It does not change the no-start decision or authorize reuse.

## Preserved inconsistencies and limits

- `FREEZE.json` contains a placeholder `source_commit`. Its retained
  `source_manifest_sha256` currently matches the exact bytes of
  `SOURCE_MANIFEST.json`, despite the contrary assertion in `STOP.json`; the
  STOP assertion is not corroborated by the preserved tip. The freeze's
  candidate/auditor fields are `1/1`, while STOP records formal
  candidate/auditor/Docker invocations as `0/0/0`; the manifest separately
  records one host construction candidate/auditor invocation and formal
  status `NOT_RUN`. Preserve this ambiguity; do not reinterpret 1/1 as formal
  execution.
- `STOP.json` initially cites an expired window; this reason is explicitly
  withdrawn by `STOP_CORRECTION.json`. Keep both files as immutable history.
- The 3/3 host construction tests and retained synthetic construction raw are
  not the planned formal Docker experiment and do not evaluate the hypothesis.
- No scientific PASS, failure, or live-runtime result is claimed. Do not rerun
  this consumed/relinquished allocation or infer authorization for a successor.

## Preservation validation

The 13 source-package files are copied byte-for-byte from branch tip
`6599fb84a7b2daf04156d4076d47f1e4ba687b80`. This PR adds only this separate
qualification document. No candidate, auditor, construction test, container,
GUI, model, or input experiment is run as part of this archival integration.
