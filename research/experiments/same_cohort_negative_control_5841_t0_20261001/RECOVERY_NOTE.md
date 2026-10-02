# Issue #5841 pre-candidate STOP recovery

This package preserves a distinct parallel worker's frozen source and exact collision STOP. It is provenance only; the candidate and auditor were not run for this allocation.

## Allocation and outcome

- Source branch tip: `01896c1fe8` (`research/5841-same-cohort-negative-control-t0-20261001`).
- Freeze: `ISSUE-5841-T0-HOST-20261001-01`.
- STOP: `STOP_PARALLEL_RESEARCH_COLLISION_BEFORE_CANDIDATE` at `2026-10-01T07:01:35Z`.
- Candidate invocations: 0. Auditor invocations: 0. Raw artifact: absent. Scientific disposition: `NOT_EVALUATED`.
- Reason: an overlapping six-case/48-row T0 was already active in PR #5858. The worker stopped rather than duplicate candidate and audit execution.
- The overlapping T0 and path-specific T1 were later consolidated by merged PR #5872. The distinct STOP source directory was absent from current main at recovery time.

## Preservation checks and boundary

- All eight original files are staged byte-for-byte from source tip `01896c1fe8`; no original file is edited.
- `STOP.json` SHA-256: `85bba25a04517519cf092703f8bb859e42728ee0a5d034c24738229ee4f089ae`.
- The source snapshot contains original CRLF line endings. A whole-package `git diff --check` reports those carriage returns as trailing whitespace; they are retained unchanged so the frozen source bytes and hashes are not rewritten. The new recovery note/index patch passes its scoped whitespace check.
- The overlapping PR's reported synthetic result is not an independent replication. This STOP adds no PASS/FAIL evidence and does not change the T0/T1 results or known primary-only export blind spot.
- No candidate, auditor, fixture builder, container, GUI, or model entrypoint was run during this recovery.

The owning Issue #5841 remains open. Any new experiment must use a distinct frozen question and allocation; this archive does not authorize a rerun.
