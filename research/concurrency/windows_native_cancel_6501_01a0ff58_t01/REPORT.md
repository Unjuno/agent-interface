# Windows one-shot native ReadFile cancellation T01

Exactly three frozen first cells ran14:26:45.324186–14:26:46.547910UTC, Windows11 build26300/CPython3.12.14, child2816/35196/16560, all exit0/no timeout. Dedicated pipe and exclusively owned one-shot native thread per cell; no pooled-thread reuse. Three sampled pending witnesses precede each action. Source/protocol/supervisor/original auditor/Python binary frozen, selected kernel32/python312/ucrtbase match C01.52 events total; original bytes and receipts retained.

| Policy | Primary caller | Primary underlying ReadFile | Later cleanup |
|---|---|---|---|
| normal D | done, not cancelled | TRUE/count1/data44 | joined; handles/FDs closed |
| asyncio wrapper task.cancel | done, cancelled | unfinished through declared500ms observation window | D cleanup delivers44; joined; closed |
| CancelSynchronousIo | not yet done, not cancelled | FALSE/error995/count0/no data; worker done | noD; joined; caller finally done; closed |

Native cancellation API returned TRUE/error0, but the conclusion uses the separate actual ReadFile completion and join. Native caller_done=false while worker_done=true at primary snapshot is retained: callback delivery scheduling differs from operation completion. Each completed reader joined before the sole native thread handle closed; both CRT descriptors proved EBADF. No live child/shared resources/input/model/GPU/runtime/main operation.

Frozen saved-data auditor first ran14:27:09.266864–14:27:09.317356UTC/PID24508 exit0. Nine serialized-effective controls exposed two first false accepts: wrong read-return native thread ID and bool sequence0 alias. Original audit source/result/control bytes/streams/actual PIDs are retained. Separate v2 adds exact typed sequence, native read/exit/join identity, final caller, and source/freeze/dependency/stream custody checks; actual14:29:33.353470–14:29:33.402969UTC/PID26100 exit0 on original unchanged data. All same nine mutations are refused by v2; no producer/native/formal cells repeated and no gates relaxed. PASS_H is this one synthetic row per policy, not independent-nonauthor review or exhaustive audit soundness.

Native ReadFile is explicitly different from C01 CRT os.read and Linux/macOS cancellation experiments. Thread-level pending flags are sampled and transient; exclusive lifetime is essential. This is no arbitrary I/O, pool reuse/fencing, atomic file-specific entry, task effect, authority, finite application recovery, practical latency/resource advantage, portable cancellation or runtime adoption result. Fixed order/uncontrolled load/one row per policy preclude performance inference.500ms is the predeclared observation window, not an estimated distribution. First original allocation remains consumed.

Primary contracts: [CancelSynchronousIo](https://learn.microsoft.com/en-us/windows/win32/api/ioapiset/nf-ioapiset-cancelsynchronousio), [ReadFile](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-readfile), [GetThreadIOPendingFlag](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-getthreadiopendingflag). Parent6501 claim5970043999/result5970114246. Dedicated inert archival review does not change existing7089 C01 source/proposal or historical comparisons.
