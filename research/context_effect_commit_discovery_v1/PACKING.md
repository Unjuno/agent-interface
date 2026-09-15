# Evidence retention note

A complete local evidence archive was produced after the four frozen allocations.

Whole archive SHA-256:

`4e55729ae7a28464d98d81601072f1951404c4624d6210e2911002b51501e039`

The archive contains all four run directories, raw JSONL, effect/rejection receipts, Xvfb logs, frames, manifests, runner sources, per-rung audits, cross-run audit v2, corruption tests, imported source snapshots, `AGGREGATE.json`, and `REPORT.md`.

The GitHub research branch intentionally retains the readable runners, aggregate, report, and independent audits. **The binary raw-evidence archive is not stored in GitHub by this commit.** Do not treat the branch as byte-complete raw retention. The local/archive artifact must be retained separately if the row-level raw evidence is required.

Offline validation of an extracted complete archive:

```bash
python audit_all_v2.py .
python corruption_check.py
```

Python bytecode caches are excluded. No font files are included.
