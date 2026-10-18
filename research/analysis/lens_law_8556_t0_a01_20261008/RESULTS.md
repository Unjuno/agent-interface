# Results

The frozen finite model produced 12 rows and the independent truth-table auditor passed. Four mutation controls were rejected. The targeted seeded defects were detected by their corresponding scoped law, while every declared out-of-scope/stale/incomplete case abstained instead of passing.

| Fixture | Outcome | Key evidence |
|---|---|---|
| valid-set, benign-hidden, completed | PASS | all three scoped laws hold |
| wrong-field, ignored | VIOLATION | Put–Get false; final-label baseline false |
| duplicate-callback | VIOLATION | Get–Put and Put–Put false, while final label matches |
| first-write-wins | VIOLATION | Put–Put false, while single-write final label matches |
| lossy-projection | UNKNOWN | applicability differs within one observed-view class |
| stale, pending | UNKNOWN | stale epoch or incomplete operation |
| partial, counter | NOT_APPLICABLE | declared partial domain or non-idempotence |

The replay comparator is a deliberately weak same-input/same-initial-state determinism check; it reports consistent replay even for the seeded defects and is not claimed to be a general metamorphic-testing baseline. This supports only the method contrast in these fixtures, not superiority on real adapters.

Machine-readable candidate rows, audit result, frozen input and truth are colocated with the source. See RUN_RECORD.md and PROTOCOL.md for execution and scope.
