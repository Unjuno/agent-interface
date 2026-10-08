# Native macOS owned-read completion boundary

Allocation: `6501-MACOS-READ-CANCEL-A01-20261003-01a0ff52-93c2`.
Parent #6501; #57's finite adapter-I/O recovery requirement is the integration reason.
Original Linux #6915, Windows #6897, Mac co-ready #6927 and the concurrent Linux FD-lifetime allocation remain separate and are never replayed.

H/T/D/C/U and the fixed eight-row roster/order/limits are in PROTOCOL.json.
No scalar wrapper completion is treated as underlying operation, descriptor, thread, input release or task completion. A logical worker-enter event is not native-kernel blocked-syscall observation. Caller-visible close is recorded independently; it may itself remain pending on this OS. Unexpected, contrary and incomplete first data remain retained.

Use selected native macOS27.0.1/arm64 CPython3.14.5. Eight serial fresh private child processes own their anonymous data/control descriptors and one executor thread; caller-close alone adds one owned closer. asyncio's internal event-loop resources are private too. No container, daemon, GUI, GPU, keyboard/mouse, model, API, network experiment or shared lease. Snapshot fields are source-ordered observations, not an atomic kernel snapshot. No descriptor is reallocated within a child. Caller and worker close roles are explicit, with no second closer for the same pipe endpoint.

Before freeze: one normal-data-only primitive construction, then independent reader over that excluded record; AST source checks. Construction source is retained and not falsely attributed to later source bytes. New selector FD EBADF observation is an additive prefreeze measurement and has no comparative execution yet. Setup path/index mistakes are retained in SETUP_FIRST_FAILURE.json; no commit of staged/unstaged base deletions is allowed.

After source/plan/oracle/environment freeze/readback: exactly one `producer.py --produce NEW_EMPTY_OUTPUT`, one raw-only primary `audit.py NEW_OUTPUT --protocol PROTOCOL.json --producer-sha FROZEN_SHA`. Each child3s, overall30s, per-child128KiB/raw1MiB; first incomplete stops deck and is never retried. The frozen controls.py defines ten full-deck copied corruptions; before freeze, the excluded retained normal-data row passes the independent reader and five typed/actor/result/ownership/final-FD corruptions are rejected. Copy-only controls are ordinary audit checks, with synchronized raw/stdout/footer/hash changes so semantic mutations cannot fail merely because of a stale checksum. Original raw/source/receipts/outcomes remain untouched. No actual performance or general portability inference is permitted.

| Symbol | Japanese meaning | SI unit and stored unit | Definition and type |
|---|---|---|---|
| ns | 各子プロセス内のイベント観測時計 | s; integer ns | perf_counter_ns, nonnegative integer scalar, not cross-process causal time |
| seq | 同じログlockで付与したイベント順序 | 1 | consecutive nonnegative integer scalar |
| pid | 所有する子プロセスの識別子 | nonphysical ID | positive integer scalar, scoped to this execution |
| tid/native_tid | Python/OS thread識別子 | nonphysical ID | positive integer scalar; not an authority token |
| fd | 子プロセス内の記述子番号 | nonphysical ID | integer scalar >2; identity includes pid and lifetime |
| rep | 固定された実行条件の反復番号 | 1 | integer0/1; finite directed coverage, not a reliability estimate |

Python's documented running-Future cancellation limitation motivates the boundary, not a measured Mac guarantee: https://docs.python.org/3.14/library/concurrent.futures.html#concurrent.futures.Future.cancel . The consulted current3.14 documentation reports3.14.8; this experiment pins the actual local3.14.5 source/runtime separately. `asyncio.wrap_future` is the wrapper used: https://docs.python.org/3.14/library/asyncio-future.html#asyncio.wrap_future . No quotations or library defect claim.

Construction producer source was recovered from the exact own original tool payload and matched its retained SHA25605192929384b199d223dcb92ea070aeefb5ad7958848f3a44364894a4f5b215c. Failed recovery attempts are preserved; no OS experiment was rerun.

Pre-freeze latest main636986a804a6004cd047db7e8cc5e62c02d585d8 differs from sourcebasefb556b3 only in additive integration evidence; governing docs/.github/root attributes/concurrency inputs are unchanged. The stdlib-only protocol does not require latest main at formal execution. All47 parent comments include no superseding allocation of this Mac boundary; #6942 now publishes the separate Linux FD-reuse result.
