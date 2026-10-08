# WAL snapshot write-recovery: native compatibility C03

The active transaction flag and primary BUSY category do not establish that a requested increment is pending. Six new private native SQLite DBs compare old/fresh read snapshots and three explicit diagnostic policies. This is known API compatibility evidence for narrow recovery routing; no new runtime mechanism or task authority is introduced.

| Read snapshot | Diagnostic policy | First write | Final revision |
|---|---|---|---|
| Before other writer commits | COMMIT only | BUSY_SNAPSHOT517, local0/external1 | 1 |
| Before other writer commits | One same-transaction write repeat, then COMMIT | Both writes517 | 1 |
| Before other writer commits | ROLLBACK, new BEGIN, new UPDATE, COMMIT | Original write517; new write succeeds | 2 |
| After other writer commits | COMMIT only | Successful pending increment | 2 |
| After other writer commits | One same-transaction write repeat, then COMMIT | Both writes succeed | 3 |
| After other writer commits | ROLLBACK, new BEGIN, new UPDATE, COMMIT | First increment discarded; new one succeeds | 2 |

Each first snapshot failure is OperationalError/SQLITE_BUSY_SNAPSHOT517/message database is locked, primary BUSY5, with active read transaction but no staged increment. The other connection already committed its increment and closed. Waiting for that writer or COMMIT-only cannot deliver the failed increment. The fixed same-snapshot repeat also fails; a fresh successful repeat produces a duplicate instead. COMMIT success alone is therefore insufficient effect evidence. Reset/new-write diagnosis is authorized only for these invented DBs, and grants no permission to repeat a cancelled, expired, uncertain or consequential real task.

SQLite documents refusal to upgrade an obsolete WAL snapshot and ending the old transaction before a new write: https://www.sqlite.org/isolation.html . Extended517 has primaryBUSY5: https://www.sqlite.org/rescode.html#busy_snapshot . Read2026-10-03. This agrees with existing specifications, and limits transfer from C02/#7044's distinct known pending-write COMMIT_BUSY state. Original C01/#6925 and7772/#7073 remain untouched.

H/T/D/C/U are in PLAN.md/PROTOCOL.json. Source/environment freeze13:35:25.210144 UTC SHAe82304a4bc9f423cf02eb021704a8f01a8092ba9f43f31bda086c51844a092e1 precedes sole producerPID27936 at13:35:46.510123–13:35:47.084921 UTC exit0. Raw SHA10498e5745599fb4274aaed67458cc2ccda35e0a362fe1cf7662663bfcb34ac0. Windows build26300/CPython3.11.9/SQLite3.45.1, exact executable/_sqlite3.pyd/sqlite3.dll/stdlib source hashes and compile options frozen. Kernel binary and global load are not frozen; times identify custody, not performance.

Six fresh endpoint children exited0, reported integrity ok, and unchanged complete closed DB bytes. All six8192B DB capsules, every endpoint full native stream/PID/UTC/exit and original50 SQL-operation records/complete SQL traces remain. Their post-operation measurement SELECTs establish snapshots after BEGIN; this is explicit instrumentation, not absence of observer intervention.

First independent saved-data implementation PID19692 at13:35:58.172306–.312470 UTC exit0 reconstructed all six endpoints and refused six controls. Preserve that first PASS and source. Later own pure-function copied-data checks showed its SQL prefix classification accepts WRONG_TARGET and WRONG_BEGIN_MODE when the retained SQL trace is changed consistently. Original data/producer are unchanged. New V2 reader enforces exact frozen label-to-SQL content, and PID22908 at13:39:34.074683–.199420 UTC exit0 reconstructs all50 events/6 closed DB copies and refuses all8 effective complete-copy controls. V2 is same-author implementation diversity, not a second human vote. See SQL_CONTROL_WITNESS.json, both audit results/controls/sources/freezes and FIRST_ERRORS_AND_LIMITS.json. Original auditor main and native producer are not rerun. Repair quoting/missing-file construction errors remain qualified; their independent full native streams/start times were not captured and are not reconstructed.

Scope: six deterministic separate-connection invented-counter cells; no shared cache, lost response, crash, real task/input authority, physical GUI effect/release, deadline/cancellation races, throughput/model/token benefit, population frequency or #6526 H_PASS. Native Windows CPU compatibility is permitted by FINAL-v5; this is not a WSLc/container result or broad portability claim. No consumed formal/native/GUI/model/peer allocation replay, runtime or workflow change, shared lease or main request. All preserved Python source has inert .py.txt names; no test discovery/import/workflow entry is added.

To revalidate retained evidence, restore the inert V2 source in a new private directory with protocol/raw and decoded exact DB capsules, then supply the recorded native endpoint streams and witness. Never replace original data or reexecute the original producer for audit. Any new construction needs a separate ID/source/environment freeze and fresh DB output. Reviewable additive delivery is separately subject to FINAL-v5 genuine nonauthor content agreement and actual-current combination/application gates.

Parent6526 claim5969647627. Fixed content base7c372cf6bea675f92939f861f34c8b0a192986dc; dedicated research/wal-snapshot-recovery-6526-01a0ff58-20261003. No retrieved identical owner in bounded all-state/branch intake; unpublished work remains unknown. Broad computer-control goal remains unresolved.
