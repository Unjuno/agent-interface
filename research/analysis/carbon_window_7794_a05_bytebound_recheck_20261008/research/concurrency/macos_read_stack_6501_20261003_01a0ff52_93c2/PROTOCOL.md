# Prospective native read-stack qualification under #6501

Worker:01a0ff52-93c2-7272-9fbc-2d01287bc6aa; policy FINAL-v5; parent6501/#57/#59.
Allocation:6501-MACOS-NATIVE-READ-STACK-A01-20261003-01a0ff52-93c2.
Reference source base:e5270c7bfe50911225afc6c3b5273021331b2bb1.
Exclusive output:@WORKSPACE@/work/macos-read-stack-formal-A01; exclusive supervisor directory with suffix -supervisor.

## H: concrete remaining interpretation

Previous own6949 caller-close EOF observations had only Python/frame/Future attribution. The new sensing condition tests whether the same outcome persists after native user-space sampling attributes _Py_read and a libsystem_kernel read/read_nocancel stub to the exact owned read-worker ID/name. In particular, the wrapper-only reference may cancel its asyncio Task while leaving that native read/Future running. Existing data and writer EOF are strong simple controls. No cancellation implementation is changed or proposed for adoption.

## T: one prospective comparison

Four serial fresh peers, fixed order reader_close, normal_D, writer_EOF, wrapper_cancel; exactly one per cell, one producer and one primary independently implemented saved-byte auditor, zero formal retries. One private pipe, one read worker and pre-created asyncio loop per peer; peer stdin is separate owned IPC. The read worker publishes its native ID/name and its only intended os.read(fd,1) call, and remains pending with the data writer silent/open. Only its owned PID is sampled via /usr/bin/sample PID 1 10 -file REPORT:1 second duration,10 ms interval,5 second process guard and1MiB report ceiling. The actor is withheld until the sampled PID/parent, exact worker ID/name, >=20 weighted _Py_read samples and >=20 read or __read_nocancel libsystem_kernel stub samples in that same worker block qualify. The main thread is excluded. Recheck the same Future pending and writer open before ACT; no data writes precede ACT.

One reader-close is executed by a separate owned close actor without retry; normal_D writes one0x44 byte; writer_EOF closes the owned writer once; wrapper_cancel only cancels the asyncio Task. The primary snapshot occurs at least250ms after the actor request. Harness release/write/close/join starts only after the primary frame, is labelled separately, and cannot count as cancellation. Ready/pre/primary/final IPC waits2/2/3/3s; peer exit2s; owned read result1s and closer join1s during cleanup. The outer supervisor owns a new process group and has a90s producer guard,10s auditor guard; only that group's children may be terminated on guard expiry. One-shot output creation and intent receipts prevent ordinary accidental re-invocation; this is no fleet-wide lock or authorization mechanism.

## D: gates fixed before comparative observations

METHOD PASS requires all four exact roster cells, attributed stack before actor, literal native and IPC bytes/hash joins, same pending Future/pre-actor live pipe, typed causal events, separate primary versus harness phase, real controls D/EOF, terminal owned peers/samplers, joined worker/closer and both final FD lifetimes EBADF. A missing sample/name/count/identity or pre-actor condition causes FIRST STOP:retain first row and later NOT_RUN, no actor on a failed stack gate, no permission escalation or identical retry. Any primary auditor failure stays FIRST FAIL with its original bytes; a later saved-only version may diagnose it without replay.

When the method passes, reader_close READ_EOF before primary with the writer still open and reader close completed supports H1 only for this observed native environment. Another completed native read kind contradicts that selected EOF hypothesis and is retained; still pending at primary is a scoped pending observation with UNKNOWN eventual native termination until separately labelled harness release. Wrapper cancelled/native Future pending supports H2; contrary Task/native state fails its comparison control and is retained. No parser/auditor PASS alone proves H1, kernel entry, a total deadline, performance, correctness of a real task or portability.

## C: alternatives and controls

Sampling can perturb scheduling; one sequential observation per actor has no independent repetitions or estimated failure rate. A global search would mistake the main stdin read for the worker read: excluded C01 has84 main-read versus84 worker-condition-wait samples and is an actual wrong-thread negative control. Ten saved C01 copy controls refuse wrong worker/PID/parent/name/type/count and missing native stub. A specially renamed main block in one DATA-ONLY copy exercises the independent parser; it is explicitly not native worker evidence. Healthy D and writer EOF separate ordinary completion from wrapper cancellation. An EOF after a Mac reader close may be host-specific and is never inferred on Linux/Windows. Final executor thread exit is separate from primary Future completion.

## U: limits

A sampled user-space syscall stub is stronger attribution than a Python frame but weaker than a complete kernel entry/return trace. No kernel tracing privilege, physical input, GUI/application/model/scorer, shared Engine/GPU or new AI worker is used. Process/FD lifetime is inferred from controlled source and exact event identities; the sampler itself exposes no FD arguments. Native Python3.14.5 and selected18 external byte pins plus OS/build are recorded; full transitive OS/dyld shared-cache and kernel identity remain incomplete. Monotonic values share one physical host/time origin; UTC is provenance. Guard values are configured maxima, not physical real-time guarantees. Prior6949 consumed allocation, sources, raw and decisions are unchanged. C01 and its method controls are ordinary excluded construction; formal counts were0/0 at source freeze.

## Variables and units

| Symbol | Meaning in Japanese | SI unit | Definition and range | Type |
|---|---|---|---|---|
| n | 試験条件数 |1| four fixed serial cases | integer scalar |
| s | スタック内のサンプル重み |1| integer20 or greater, no larger than its selected thread root | integer scalar |
| d | ネイティブサンプラーの設定時間 |s|1 | real scalar |
| i | ネイティブサンプラーの設定間隔 |s|0.010 | real scalar |
| c | actorからprimaryまでの観測間隔 |s| actual monotonic delta, minimum0.250 | real scalar |
| t | 単調時計の時刻 |s| recorded integer nanoseconds divided by1e9 | integer encoded scalar |
| fd | 所有する記述子番号 | nonphysical identifier | bound to peer PID and declared reader/writer lifetime, never integer-only ownership | integer identifier |
| pid | 所有するプロセス識別子 | nonphysical identifier | strict positive integer bound to source invocation | integer identifier |

This packet is an inert research source/evidence snapshot (.py.txt) with no runtime/discovery/workflow entry. Exact source commit/tree are external freeze records to avoid self-reference.
