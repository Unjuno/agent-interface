# Recovery qualification — Issue #4588 synthetic first-rung probes

## Provenance and scope

This additive archive preserves the eight original files from branch
`research/issue-4588-confidence-trajectory-first-rung-20260927` at commit
`4e9090373f15235033aff53e5d2e316239e6bd71`. The source preregistrations,
probes, result reports, and aggregate metrics transcription are unchanged.
The two subdirectories describe distinct allocations; do not pool them.

These are also distinct from the separately documented 84-case
`confidence-trajectory-4588-first-rung-20260927-01`, the
`confidence-trajectory-system1-v1` allocation, the learned-head archive in
PR #4610, and later #4597 successor work.

## Evidence boundary

The recovered branch contains no immutable `FREEZE.json`, no per-case formal
raw output, no independent audit report, and no `OBSTAC_*` run-receipt metadata.
`METRICS_TRANSCRIPTION.json` is an aggregate transcription, not the original
runner output. Consequently these outcomes are preserved as historical
branch-reported results, not independently reproduced or OBSTAC-attested
formal evidence. Disposition for this recovery is
`HOLD_RECOVERY_RAW_AND_PROVENANCE_INCOMPLETE`.

- v1 reports `FAIL_INTEGRITY`: its source draws irregular time intervals inside
  the scenario loop, so nominally paired scenarios do not share timing. Its
  aggregate metrics are descriptive only, not a valid paired comparison.
- v2 reports `HOLD_NOOP_STALL_RISK` and
  `HOLD_ACCEL_NOT_BETTER_THAN_VELOCITY`. The reported result does not support a
  general action-selection benefit. Its original per-case rows are absent.

No formal run, probe execution, raw reconstruction, metric replacement, or
result relabeling was performed during recovery. The existing H/T/D/C/U,
limitations, and two result reports remain authoritative for the claims they
make; this note only qualifies their recoverability and integration status.

## Local preservation checks

The eight original files are carried from the exact source commit above. The
recovery check may parse the aggregate JSON and compile the two Python sources,
but those structural checks do not validate either scientific outcome. Any
future attempt to reproduce this question requires a separately frozen
allocation with complete raw capture and the repository's OBSTAC provenance
fields; it must not reuse or overwrite these historical allocations.
