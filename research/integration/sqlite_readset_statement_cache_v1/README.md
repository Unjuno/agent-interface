# Retained SQLite read-set / statement-cache experiment

Read REPORT.md first. This is an additive research bundle, not a runtime patch.
Parent questions: #1713 and closed #501. No remote Issue/PR has been created by
the executing connection. ISSUE_DRAFT and PR_DRAFT are explicitly unsubmitted.

**Local first-outcome result:**60 cases in10 immutable batches;
PASS_SQLITE_READSET_CACHE_BOUNDARY_SCOPED. EVENT_ONLY has10 missing dependencies
and2 stale private results. Disabling statement cache prevents those but has2
false refusals. METADATA_REUSE has0 omissions/stale results/false refusals in its
20 cells. No GUI, model, latency/token, security, production or arbitrary-SQL claim.

EVIDENCE.tar.xz and CAPSULE.json retain ALL2579 original source/raw/construction,
STOP/test-failure/gate-failure, freeze, database, process, audit and control files.
Construction is not pooled with formal. The original proposed precision gate
failed during construction and remains visible; the formal gate was frozen
only afterward. This is local, construction-informed preregistration, not a
publicly preregistered or blind replication.

## Offline review, no experiment rerun

Require Python with SQLite support. The original execution used CPython3.13.5 /
SQLite3.46.1 on provided Linux x86_64, not Docker/OrbStack. Use fresh paths:

```sh
python -B restore.py /tmp/sqlite-readset-review
python -B /tmp/sqlite-readset-review/audit.py \
  /tmp/sqlite-readset-review/formal-01 --out /tmp/sqlite-readset-audit.json
cmp /tmp/sqlite-readset-review/AUDIT.json /tmp/sqlite-readset-audit.json
python -B /tmp/sqlite-readset-review/corruption.py \
  /tmp/sqlite-readset-review/formal-01 --out /tmp/sqlite-readset-controls.json
cd /tmp/sqlite-readset-review
python -B -m unittest -v test_policy
```

restore.py validates archive size/hash, member counts, bounded expansion and
all member byte digests; it refuses links, path traversal and existing output.
It executes no archived code. Checksums bind integrity, not authenticity.
The auditor uses read-only SQLite connections and never starts worker/peer.
Corruption controls copy individual cases into private temporary directories;
each intact relocated baseline must pass first. They rebuild local byte bindings
and require specific independent semantic rejections. This is not a proof that
arbitrary forged evidence or every gate alteration is detectable.

DO NOT rerun the consumed formal-01 allocation. runner/supervise are retained
for source inspection; a genuinely new allocation needs a new frozen identity,
exact environment and current collision/publication checks. No new engineering
Issue is required merely for a transport or wrapper failure.

## Integration/review boundary

Directly readable policy, driver, peer, auditor, tests and proof accompany the
capsule. No shared runtime, workflows, root direction or predecessor is edited.
Local patch validation uses an empty/minimal staging tree, NOT the full repository
CI. Before actual remote publication inspect current main/ownership and relevant
repository checks. This branch/PR is a suggested additive delivery, not a merge
claim. No foreign or unpublished branch was deleted.
