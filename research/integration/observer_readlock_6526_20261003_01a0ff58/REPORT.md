# Retained result and audit failure

One native comparison recorded all16 conditions with exit0,04:07:13.812683 to
04:07:15.012956UTC on2026-10-03. Windows CPython3.11.9 and SQLite3.45.1 are
source/build qualified by the prospective C01 freeze and source commit
61b15afd2d5696c70a7523127ee655c70922c083. No timing-performance inference is made.

| Journal | Observer | Conditions | COMMIT | Fresh persisted endpoint |
|---|---|---:|---|---|
| DELETE | none / short target / held SELECT1 | 6 | success | desired text, revision1 |
| DELETE | held target | 2 | SQLITE_BUSY; explicit rollback | old, revision0 |
| WAL | all four policies | 8 | success | desired text, revision1 |

Both held-target WAL observations remain old/revision0 before and after the
successful writer commit; separate fresh scorer processes see desired/revision1.
Every writer updated one private row, attempted COMMIT once and used busy_timeout0.
Every active observer used mode=ro/query_only1 and changed zero SQL rows. Native
SQL traces and connection-close events distinguish UPDATE, COMMIT and fresh effect.
This demonstrates finite observer intervention under rollback journaling and a
separate held-snapshot freshness boundary. It is a transfer of known SQLite
semantics, not a new theorem, measured GUI effect or production-app diagnosis.

The original frozen auditor **failed with exit1** at04:07:21UTC: it incorrectly
required no sidecars after closing connections. That source/raw/first exit are
retained. All8 WAL rows actually record -wal/-shm. Four held-reader bundles still
contain4152-byte WAL files; a main-DB-only archive would omit committed state.
The remaining4 WAL files are empty. SQLite documents that WAL belongs to the
database's persistent state and can outlive connections:
[WAL documentation](https://www.sqlite.org/wal.html).

R01 is ordinary retained-audit repair, not a candidate rerun. Separately frozen
audit_v2.py first ran once at04:15:34UTC, exited0, reconstructed16 conditions from
unchanged raw and exact copies of complete DB/WAL/SHM bundles, and rejected8
effective copied-raw and3 custody corruptions. Original source/trace/lifecycle,
typed counts, fresh-process endpoint, DB byte hashes and payload gates remain.
Only the false no-sidecar assumption changes to the actual recorded roster plus
complete native custody validation. Snapshot sidecar hashes were captured after
the original auditor failed; they are **not original end-time custody hashes**.
The source snapshot is never opened by SQLite during v2; fresh copies are used.

Original first-audit disposition stays FAIL. V2 supports a qualified finite
retained reconstruction and cannot retroactively pass C01's original audit,
repair missing first custody records, override #6526 HOLD_AUDIT_TIMING, or prove
GUI H_PASS. Historical A01/A02/A03 and #6921's publication intervals are unchanged.
No container/WSLc, GUI/browser/input, model/GPU, game, production runtime,
mandatory check or existing index was modified or invoked by this study.

The32 native files are transported losslessly as custody/native/*.b64, with both
encoded and decoded hashes. Run `python restore.py` once in a fresh writable
private copy to reconstruct them. The complete late snapshot is the evidence;
do not discard the nonempty WAL. Inspect the already retained audit-v2.json and
four command receipts. A reviewer may implement a separate retained-data check;
the original producer and consumed first auditor need not be executed.

One exception's public stderr replaces only the private task-root path with
<STUDY_ROOT>. publication.json binds original and published bytes; the original
unredacted stderr remains privately retained. The historical command receipt
hash identifies the original stderr, while the package manifest identifies its
public derivative. There is no claim that these hashes are identical.
