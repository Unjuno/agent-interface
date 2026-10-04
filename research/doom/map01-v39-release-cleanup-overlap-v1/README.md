# MAP01 current-v39 cleanup-overlap construction

Construction follow-up to PR #7378 and Issue #59. See `PLAN.md` for H/T/D/C/U
and limits. `RAW_CANDIDATE.txt` records the container test run. This is a
synthetic adapter test, not the separately gated live release allocation.

The test asks whether a verified `owner_release` cleanup timestamp falls
inside each explicit `up` call's monotonic bracket. Missing records fail
closed. The test keeps the one-batch sample/publication behavior from PR #7378.

The first WSLc log auditor and its output are retained but superseded: it only
searched for expected pass strings. The corrected host-side audit parses one
terminal unittest summary, checks the retained exit receipts, and rejects
contradictory-summary/exit mutations; see `results/RAW_AUDIT.txt` and
`results/RAW_AUDITOR_TESTS.txt`.
