# Executor callable lifetime boundary — #6501

Worker `01a0ff35-0b9f-7d13-bcfa-22d064ff4fec`, FINAL-v5; base
`cb13a10dce358649458f5aea00947b8aa43fc5b8`. New ordinary native construction,
not a replay of T0/T0b/#6890 or the socket-scope allocation.

H: cancelling the last shielded waiter makes an asyncio wrapper terminal while
its already-entered executor callable still runs. Removing that scope entry on
wrapper cancellation permits overlapping replacement work. Retaining CLOSING
until the underlying concurrent Future is actually done prevents this overlap.

T: two policies × four Event-barrier schedules = eight rows. Policies differ only
in cancellation retirement: wrapper-terminal removal vs concurrent-Future done
acknowledgment. Schedules: two stable waiters; one detach plus rejoin while the
other waiter remains; both detach plus rejoin before exit; both detach followed
by rejoin after exit. Every producer is a tiny synthetic read-only callable,
with one gate, bounded 3-second wait, at most two executor threads. Each row uses
a fresh executor. Counts and serialized event order are actual observations.
No sleep-duration/timing performance comparison or arbitrary schedule inference.

D: expected source calls / delivered / cancelled / yielded / peak active:

| Schedule | Wrapper-terminal policy | Future-ack policy |
|---|---|---|
| stable_pair | 1 / 2 / 0 / 0 / 1 | 1 / 2 / 0 / 0 / 1 |
| one_detach | 1 / 2 / 1 / 0 / 1 | 1 / 2 / 1 / 0 / 1 |
| early_rejoin | 2 / 1 / 2 / 0 / 2 | 1 / 0 / 2 / 1 / 1 |
| post_exit_rejoin | 2 / 1 / 2 / 0 / 1 | 2 / 1 / 2 / 0 / 1 |

Both last-detach checkpoints must observe wrapper done/cancelled while the
underlying Future remains running/not done and one callable remains active.
Candidate must retain its CLOSING entry at that checkpoint. Independent raw-only
audit reconstructs producer/caller identity, attach/detach, enter/exit, wrapper/
Future completion and cleanup from every ordered event, not authored summary
counters. Every row ends with zero active callables, done wrappers/Futures,
empty registry and joined executor. Missing/extra/type-altered/duplicate rows,
invalid event/caller/producer/order or incomplete cleanup are HOLD.
PASS_THREAD_LIFETIME_SCOPED requires all eight expected rows and corruption
controls. Unexpected execution failure is retained FAIL/HOLD; matrix cap=1,
retries=0 for this frozen source/output. Ordinary construction tests are separate.

C: barriers expose a boundary deliberately; overlap is not production prevalence.
The strongest simple comparator is standard shield + a last-detach counter with
early task cancellation. Standard concurrent Future completion is the candidate's
existing primitive; no thread kill, new scheduler or semantic authority is added.

U: sequential registry access in one event loop, one synthetic full-scope key,
trusted entered/exited callable lifecycle, native Windows CPython 3.11.9. This
does not preempt indefinitely blocked/noncooperative real I/O, prove OS-thread
termination before executor shutdown, bound physical input, establish clock or
effect freshness, or measure latency/throughput/token/task benefit. CLOSING may
remain indefinitely in a real nonterminating adapter and must YIELD/escalate;
it cannot fabricate resource release. No shared runtime/container/GPU/model/GUI,
network/socket/backend/input or formal allocation. Existing studies immutable.

| Field | 日本語の意味・定義 | SI unit | Range / assumption | Type |
|---|---|---|---|---|
| sequence | ロック下で確定したイベント順序 | dimensionless | contiguous from zero within row | exact int |
| producer | 実際にsubmitした読み取り呼出しの識別子 | dimensionless | starts at one, local to row | exact int |
| active_callables | enter後・exit前の呼出し数 | dimensionless | observed under one lock, 0..2 | exact int |
| waiters | 当該entryに付いた待機者数 | dimensionless | exact attach/detach balance, 0..2 | exact int |
| WAIT_SECONDS | 構築バリアの最大待ち時間 | s | 3; a timeout is failure | exact int |

Source/oracle/input identities freeze in local Git before the matrix. Exact
stdout/stderr and UTC/exits are captured privately; public logs redact only local
path prefixes with both hashes disclosed. The first scaffold timeout is qualified
in INITIAL_SETUP.md. Fleet deadline is unknown and is neither set nor extended.

Primary sources: Python [Future.cancel/running/done](https://docs.python.org/3.11/library/concurrent.futures.html#concurrent.futures.Future.cancel)
and [asyncio shielding](https://docs.python.org/3.11/library/asyncio-task.html#shielding-from-cancellation).
Documentation distinguishes cancellation attempts and completed callables; it
does not supply this repository's measured result or certify real adapter I/O.
