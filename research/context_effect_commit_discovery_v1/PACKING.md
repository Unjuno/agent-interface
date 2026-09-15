# Evidence retention note

A complete local evidence archive was produced after the four frozen allocations.

Whole archive SHA-256:

`4e55729ae7a28464d98d81601072f1951404c4624d6210e2911002b51501e039`

The archive contains all four run directories, raw JSONL, effect/rejection receipts, Xvfb logs, frames, manifests, exact runner sources, per-rung audits, cross-run audit v2, corruption tests, imported source snapshots, `AGGREGATE.json`, and `REPORT.md`.

The GitHub research branch retains the report, compact summary, independent cross-run auditor, and corruption controls. **It does not retain the binary raw-evidence archive or the exact runner files.** Their SHA-256 values are listed in `SUMMARY.json`. Therefore this branch is not byte-complete raw retention and must not be described as independently rerunnable without the separately retained archive.

Offline validation of an extracted complete archive:

```bash
python audit_all_v2.py .
python corruption_check.py
```

Python bytecode caches are excluded. No font files are included.
