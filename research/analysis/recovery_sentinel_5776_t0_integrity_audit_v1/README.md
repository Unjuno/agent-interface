# Supplemental artifact integrity audit

This package records an integrity-only failure discovered after the v2 Docker result was merged. It does not rewrite or replace the original v1/v2 evidence.

The reproducible finding and exact byte hashes are in [REPORT.md](REPORT.md), [FREEZE.json](FREEZE.json), and [receipts.txt](receipts.txt). The committed v2 bundle's raw ledger refers to a fixture hash absent from the merged tree; the committed audit stops at that mismatch before replay.

Disposition: `FAIL_ARTIFACT_FIXTURE_HASH_MISMATCH`. No scientific re-run or substitution was performed.
