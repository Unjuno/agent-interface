# SQL scope-receipt compaction / r9t2

Retrospective publication for Issue #4429. This is research evidence only.

## Scoped result

`PASS_LOCAL_SCOPE_COMPACTION_BOUNDARY`, while **rejecting unconditional
SCOPE_ONLY adoption**.

| Receipt | Writer profile | Cases | Stale stored query results | False refusals |
|---|---:|---:|---:|---:|
| FULL | OFF | 12 | 0 | 0 |
| FULL | ON | 12 | 0 | 0 |
| SCOPE_ONLY | OFF | 12 | 4 | 0 |
| SCOPE_ONLY | ON | 12 | 0 | 0 |

The directed counterexample uses SQLite REPLACE. When writer-side
`recursive_triggers` is OFF, the old-range delete trigger does not maintain the
scope epoch; row revisions still expose the change. The finding is a dependency-
coverage boundary, not a SQLite defect.

Full original plan/source/raw SQLite databases/IPC/process receipts/auditor and
construction history are in `EVIDENCE.tar.xz`. Review without rerunning science:

```sh
python -S -B verify_capsule.py /tmp/r9t2-review
cd /tmp/r9t2-review/research/integration/sql_scope_compaction_r9t2_v1
python -S -B verify.py
python -S -B test_contract.py
```

Do not execute the consumed formal batches. See `PUBLICATION_NOTE.md` for
chronology and publication scope.
