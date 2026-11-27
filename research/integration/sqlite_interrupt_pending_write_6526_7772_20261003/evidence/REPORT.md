# 6526 pending-write interruption compatibility C01

Actual existing worker01a0ff58-7772 / FINAL-v5, prospective claim5969168458.
Ordinary private three-cell compatibility construction; no formal replay.
Disposition: SCOPED_COMPATIBILITY_PASS, a known SQLite API boundary confirmed
in this Windows CPython3.11.9 / SQLite3.45.1 build. No new algorithm or runtime
adoption. This does not complete #6526/#57/#59 or computer-control.

H: one returned SQLITE_INTERRUPT error code does not identify whether an earlier
accepted/staged write still exists. The interrupted SQL operation and actual
connection state matter. T: three fresh invented databases, explicit transaction,
one pending counter increment, target SELECT or UPDATE, owned progress handler
returning1 at interval1 for the two interrupted cells; healthy UPDATE control.
Clear owned handler, retain owner/fresh observer states, try COMMIT once only as
an authorized toy diagnostic, close and inspect in a fresh endpoint subprocess.
D: prospective source/environment/freeze defines exact read9/active1/end1,
write9/inactive0/commit-error1/end0, healthy active2/end2; otherwise retain first
contradiction/error without changing criteria. C: result follows standard SQLite
semantics, not novel cancellation/recovery; progress callback controls are not
arbitrary live cancellation races. U: SQLite DLL separate pin/OS kernel/build
identity and scheduler/load were not frozen; Python executable and extension
module bytes plus reported SQLite/Python versions were. No portability,
mid-write visibility, crash/power-loss, external interference, deadlines,
performance, GUI, physical release or task benefit claim.

| New cell | Target returned | After target: active / owner revision / fresh observer revision | One diagnostic COMMIT | Closed DB / fresh-process revision |
|---|---|---|---|---|
| READ_INTERRUPT | OperationalError / SQLITE_INTERRUPT9 | true / 1 / 0 | returns success | 1 |
| WRITE_INTERRUPT | OperationalError / SQLITE_INTERRUPT9 | false / 0 / 0 | SQLITE_ERROR1, no active transaction | 0 |
| HEALTHY_WRITE | returns success | true / 2 / 0 | returns success | 2 |

Each interrupted handler was actually called once; no target statement was
resent. Each owner SQL trace has76 entries, preserving complete seed64rows
and all transaction/target/state/commit statements. Both interrupted results
have the same Python class/code/name/message. Healthy completion is an exact
counter/database control, not successful original computer-control task effect.

The SELECT interruption leaves the earlier increment pending and locally
visible, not committed; a separate read-only observer still reads0. The UPDATE
interruption returns after rolling back the whole transaction, including that
earlier increment. A blind COMMIT cannot recreate it and explicitly refuses.
This supports checking actual in_transaction and effect/task state instead of
classifying all OperationalError or SQLITE_INTERRUPT alike. It does NOT grant
permission to commit after cancellation. Even an active transaction supplies
no current task authority. A real cancelled task may require rollback/stop;
uncertain external commits or effects require separate reconciliation, never a
new write resend based only on these known returned local outcomes.

## Actual first native endpoints and independent saved-data reconstruction

One producer PID6984, 2026-10-03T12:30:35.249446–12:30:35.778226UTC,
exit0; stdout132B SHA83f3de146f56b0b4499a8c5251ad3c8705ab361075c5e003c62528612ff58464;
stderr0B. Sources and environment frozen BEFORE this first deck. Three fresh
endpoint subprocesses5364 /10024 /30988 each actualwait exit0, full stdout/
stderr/UTC/PIDs/closed DB hashes inside RAW. DB capsules each12288B and include
all original bytes. Endpoint reads preserve before/after byte hashes.

Different saved-only SQL/state reference PID13756,
12:32:27.861267–12:32:27.938542UTC, exit0; stdout1157B
SHA05ef12929deff1cbf825df73d0104e8de247a7376ba8c7542d2b3db9e8c6cac2;
stderr0B. Its source/input/D freeze precedes its one invocation. It imports no
producer. It verifies228 literal SQL trace rows, complete source-bound state,
typed errors, staged/committed observer distinction, endpoint raw stream hashes,
DB capsule→actual-file→readonly immutable SQLite schema/counter/all64row joins,
ordered UTC intervals and actual native endpoint0. All inputs unchanged.
It rejects six effective complete copied records: bool/int transaction alias,
masked rollback, extra UPDATE, falsely successful commit, nonzero endpoint,
foreign endpoint value with recomputed stdout hash. Complete altered inputs
are retained. These are same-worker implementation diversity, zero distinct
nonauthor votes/emitter authentication. A later CIM endpoint observation found
none of the five recorded producer/endpoint/auditor PIDs; historical wait receipts
supply actual exits, not PID absence alone. No producer/auditor repetition.

## Prior studies, sources and authority

8f42 #7044/C02 known returned COMMIT_BUSY comparison remains owned and unchanged;
not rerun. #4397 query_only/WAL reader cancellation explicitly excludes writes;
its original allocation is not reused. All #6526 GUI/C01/A01/A02/A03 raw and
adjudication remain unchanged. Bounded open/closed searches and actual bodies
found no retrieved same pending-write contrast; unpublished work stays unknown.
One intake GitHub4397 read used wrong argument key and failed tool binding;
correct documented repository_full_name succeeded. Tool transcript retains that
setup failure; no request took effect and no scientific allocation started.

Official primary sources, accessed2026-10-03 before freezing this deck:
- https://www.sqlite.org/c3ref/interrupt.html — interrupted writes in an explicit
  transaction roll back the transaction; no novelty inferred.
- https://www.sqlite.org/lang_transaction.html — error response can affect the
  statement or whole transaction; inspect transaction state. The separate
  known returned COMMIT_BUSY path retains its active transaction.

No GUI/model/backend/WSLc/container/GPU/native input/shared lease or source/
ref/main modification. Three small invented DBs and stdlib, one native driver
plus three sequential endpoints, one separate saved-data reader. Times are
capture accounting only. Claim introduces no worker, reviewer vote or adoption
certificate, and carries no permission to retry a real failed/cancelled task.
