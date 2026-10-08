# Audit-v1 STOP — preserved first invocation

Frozen command: `python3 -B audit.py --raw results/raw.json --output results/audit.json`

Exit code: 1. The only invocation stopped in `_validate` at `audit.py:85` with:

```text
KeyError: 'preaudit_stream_sha256'
```

The auditor expected a flattened freeze key. `FREEZE.json` stores the stream digest in `fixture.stream_sha256` and source hashes in `source_sha256`. No `results/audit.json` was written. This is an audit-construction/schema-adapter STOP, not a scientific FAIL or PASS. The candidate raw remains unchanged; audit-v1 was not retried. A separately frozen read-only v2 schema adapter audited the same raw; see `results/audit_v2.json` and `EXECUTION.md`.
