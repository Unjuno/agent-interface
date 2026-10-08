# Retrospective GitHub publication note — Issue #4086

This directory publishes the already completed local allocation `wal-snapshot-retention-531-d90e-20260922-01`.
The formal experiment was locally frozen before execution, but **was not registered on GitHub before execution**.
No formal case is rerun, replaced, pooled, or retuned for this publication.

Scoped result: `PASS_WAL_SNAPSHOT_RETENTION_BOUNDARY_SCOPED`.

## Lossless evidence transport

`COMPLETE_EVIDENCE.patch` is the byte-identical additive Git patch generated from the retained local result.
Its Git blob is `4f38da5b0ecaa7ab36d66eada5cdd3d83bec0133`; the original patch SHA-256 is
`68114ace5180f04e7516b2dcf383b8609527753988a4b247f4bbfe02511870db`.

The patch reconstructs all 26 original publication files, including the binary
`evidence.tar.xz` (79,452 bytes, SHA-256
`964c0d6c5789ce1fb4d92ec3acaa4442be0c03f88c430cd4f0b065dcc5eac1a8`).
That archive expands to exactly 293 retained experiment/evidence files and contains its own
`SHA256SUMS` covering the other 292 members.

For a lossless read-only review, use a fresh temporary repository, not this branch:

```sh
mkdir /tmp/d90e-full && cd /tmp/d90e-full
git init -q
git apply --binary /path/to/COMPLETE_EVIDENCE.patch
cd research/coordination/wal_snapshot_retention_531_d90e_v1
python -B unpack.py /tmp/d90e-review
cd /tmp/d90e-review
sha256sum -c SHA256SUMS
python -B audit.py --controls
python -B test_contract.py
```

Do **not** rerun the consumed formal allocation merely for publication. Any live replication requires a distinct prospective allocation.

## Directly readable subset

The branch also exposes the original REPORT, README, PLAN, environment, result, frozen sources,
independent raw auditor, unit tests, FREEZE and AUDIT directly so reviewers do not need to apply
the complete patch merely to understand the study.

Scope remains narrow: one Linux/SQLite fixture, no production runtime change, no GUI/model task,
no token/latency claim, no power-loss guarantee, and no claim that historical copied evidence
creates current action authority.
