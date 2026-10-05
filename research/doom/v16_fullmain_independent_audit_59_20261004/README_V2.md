# V2 audit correction and disposition

This additive successor preserves the original `audit.py`, its output, and its
seven-test history unchanged. The V1 `PASS_SCOPED_V16_LIFECYCLE` was too broad:
the retained construction02 trace has one delivered `finish` command and a
post-control score, but no `terminal` event even though the ready contract says
terminal lifecycle closure is separate. V2 therefore reports
`HOLD_LIFECYCLE_TERMINAL_UNOBSERVED`; it does not infer completion from process
exit or command delivery.

V2 also closes two one-hold audit gaps identified in review: the nested receipt
must explicitly be `operation="up"` with `server_sync_completed=true`, matching
the owner-thread row, and the verified-empty owner sample must occur after the
release-transition emission. These are chronology/receipt checks over retained
synthetic records, not physical key-up, application-use, or game-effect claims.

## Reproduction

Run from the repository root:

```bash
python research/doom/v16_fullmain_independent_audit_59_20261004/audit_v2.py --repo .
python -m unittest discover -s research/doom/v16_fullmain_independent_audit_59_20261004 -p 'test_audit*.py' -v
git diff --check
```

Expected retained-data disposition: no V2 mutation errors, one explicit HOLD
for the missing construction02 terminal row, and all three V2 review-boundary
controls rejected by the test suite. No source experiment is rerun or altered.
