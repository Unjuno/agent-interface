# SQLite cancellation completion — #4397

Allocation: sqlite-interrupt-release-20260926-i126. Research evidence only.
Base: 4c701cc51b06296268ad8d9ae3eff1dd6f2d379d.

## H / T / D / C / U

H: interrupt return, target-query abortion, and release of a read session are
three different milestones. Only explicit termination of all owned cursors and
any explicit read transaction, followed by an observed checkpoint, supports the
fixture's WAL-reclaimed claim.

T: five states (IDLE, IMPLICIT_ONE, EXPLICIT_ONE, EXPLICIT_DONE, IMPLICIT_TWO),
three policies (INTERRUPT_ONLY, AWAIT_TARGET, FINALIZE_ALL), two repetitions.
Thirty fresh64-row databases, two separately exec'd actors each. State-major,
then policy-major, then repetition order; three ten-case batches, each once.
Construction uses16 rows and is excluded. Each actor RPC has a3s safety limit;
owned batch supervision25s, enclosing tool at least35s. No timing-speed gate.
All policies call interrupt while paused between fetches. AWAIT_TARGET advances
only the first cursor; FINALIZE_ALL ends the complete owned read session.
Use SQLite WAL/FULL/timeout0/autocheckpoint0, autocommit=True, query_only reader.
Writer changes only row0 from0 to9999 after reader preparation. No new reader
work occurs during primary checkpoint. Cleanup checkpoint is scored separately.

D: PASS_SQLITE_INTERRUPT_RELEASE_BOUNDARY_SCOPED only if all30 cases/60 actor
and3 runner exits reconcile, all sources match the public freeze, all raw
snapshot/pipe/SQL joins pass, and12 effective well-formed mutations reject.
Expected primary busy counts per10: INTERRUPT_ONLY8, AWAIT_TARGET6, FINALIZE_ALL0.
AWAIT_TARGET has6 actual SQLITE_INTERRUPT target errors;4 still retain WAL.
IDLE always reclaims; every FINALIZE_ALL and all cleanup checkpoints have tuple
[0,0,0] and zero WAL extent. Historical copied prefixes stay exact. Complete
contradictions are FAIL; missing process/source/raw/control evidence is HOLD/STOP.
Formal reruns/replacements/exclusions/post-result tuning0. Public complete source
freeze/readback is required BEFORE formal; publication failure is not permission
to relabel this allocation local-only.

C: cooperative single reader connection and writer, trusted complete cursor
ownership, no new concurrent reads, no writes on the reader, same DB identity,
successful SQLite APIs. AWAIT_TARGET legitimately stops one query but not the
whole session. Candidate cancellation abandons unread rows rather than returning
a complete query result. This is not an alleged deployed runtime defect.

U: no mid-opcode cancellation deadline, thread-race study, BLOB handles, foreign
connections, app/model/task/token benefit, physical disk recovery, power loss,
source authentication, DB rollback or production integration. Same-author
separate implementation/process audit is not independent human review. Directed
technical repetitions do not estimate natural failure probability; calibrated
combined uncertainty and a coverage factor are not available.

## Conditional reasoning

If every active reader statement belongs to the cancellation owner, closing all
its cursors finishes those statements. If the same connection has an explicit
read transaction, ending that transaction removes its independent retention.
Under the no-other-reader/no-new-reader assumptions there is then no retained
read snapshot on this connection. That proves only removal of this blocker:
checkpoint execution and its resulting extent must still be observed. The raw
checkpoint is the reclamation witness, not the interrupt or exception receipt.

Conversely, neither interrupt return nor observing one statement's error proves
that all statements and explicit transactions ended. The two pending-cursor and
explicit-transaction cases separately test these missing implications. The
experiment measures a known SQLite lifecycle contract, not a new DB theorem.

## Variables / units / definitions / domains / types

| Name | Meaning (Japanese) | Unit | Definition/domain | Type |
|---|---|---|---|---|
| state | 読取り資源の初期状態 | 1 | five fixed enum values above | enum |
| mode | 取消し完了処理 | 1 | three fixed enum values above | enum |
| n | 初期行数 | 1 | 16 construction;64 formal | integer scalar |
| rep | 指定反復番号 | 1 | 0,1 formal;0 construction | integer scalar |
| checkpoint | busy/log/checkpoint済みframe数 | 1 | observed three nonnegative integers | integer vector |
| wal_bytes | WALの見かけ長 | byte (8 bits; not SI) | actual st_size, nonnegative | integer scalar |
| start_ns,end_ns | 同一host単調時計の観測区間 | ns (10^-9 s) | recorded monotonic readings | integer scalars |
| in_transaction | SQLite autocommitに対応する状態 | 1 | measured bool; not total cursor ownership | Boolean |
| target_error | 対象SELECTの実例外 | 1 | null or recorded SQLite error/code | tagged record |

Unit check: checkpoint frame counts are not bytes. For this one-frame WAL,
apparent length is32 header bytes plus one(24 frame-header bytes +4096 page
bytes), hence4152 bytes. No physical storage allocation is inferred. Ordering
compares monotonic nanoseconds only on this host, without wall-clock conversion.

## Roadmap / reproduction boundaries

Excluded construction -> exact public freeze/readback -> three formal batches ->
separate raw-only audit/controls -> complete source/raw evidence PR -> applicable
exact-head checks and scoped review -> qualified main readback. No prior actor
rerun, no shared runtime/workflow/index change. Preserve #4116/#4086/c118/v104 and
all foreign studies. Global ROADMAP remains open.

Primary background (not experiment evidence):
https://www.sqlite.org/c3ref/interrupt.html
https://www.sqlite.org/lang_transaction.html
https://docs.python.org/3.13/library/sqlite3.html
