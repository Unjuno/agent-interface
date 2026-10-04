# #6501: FD-number lifetime and late cleanup

Allocation: `6501-FD-LIFETIME-ORBSTACK-A01-20261003-01a0ff52-70ab`.
Actual worker01a0ff52-70ab-7f10-82b3-e60375a032fb, FINAL-v5.
Scientific parent6501; claim5965896256. Source base9c26e204c0475bee30919e3d0e6681f393078ef1.

## H

An integer FD identifies its current process-table slot, not an immutable pipe
lifetime. A caller and a delayed worker finalizer can each close their copy of
the same number after it has been reused for a different owned pipe. In two
explicit Linux schedules, integer-only cleanup will close the replacement reader.
A shared lock-protected one-time ownership take before the actual close will
give only the first closer the original FD and preserve the replacement slot.
It will not itself interrupt the old blocked read. Common harness D release is
separate cleanup and is never scored as cancellation success.

This is a standard OS/ownership adapter contract test. It is neither a new OS
discovery nor a claim that any production singleflight implementation has this
defect. #6915 explicitly excluded FD reuse; #6927 owns co-ready selection;
#3984 studies duplicate regular-file offsets, #1460 logical input-generation
ABA, #4124 process/ownership-pipe lifetime and #4514 the live X11 fault graph.
None is replayed or absorbed. Bounded all-state/branch/comment intake is retained
outside the source; unpushed work and universal novelty are unknown.

## T

Exactly six rows: `integer_copies` and `once_owner`, each with caller-close/
reuse-before-worker-finally, worker-finally/reuse-before-late-caller, and normal
finish. Each row owns two fresh anonymous pipes and one fresh native reader
thread. The unrelated sentinel pipe exists before the original reader starts.
`/proc/self/task/TID/{stat,wchan,syscall}` must show aarch64 read63 of the actual
FD, stateS/wchananon_pipe_read before action. Raw omits syscall addresses/PCs.

Caller-first: close original -> still-blocked witness -> dup2 sentinel reader
into the vacated number -> close source alias -> queue R in sentinel -> actual
still-blocked witness while FD table points to new identity -> record checkpoint
-> harness queues D in original writer -> old read returns D -> worker cleanup.
Worker-first: queue primary D -> worker cleanup/native join -> reuse number and
queue R -> late caller cleanup. Normal positive: original D/worker cleanup/join,
then independent sentinel R, with no caller cleanup/reuse. All rows directly
probe the sentinel slot, distinguishing actual R from EBADF, then close current
owned resources and verify every FD closed/native TID absent.

`OnceOwner.take_for_close()` atomically replaces its retained FD with None under
a shared lock before returning the original number. It does not recreate or
rebind ownership for a later object with that number. Different rows have new
owners. Integer-only copies intentionally have two cleanup authorities. This
comparison changes only closure ownership; it is not a control-pipe mechanism.

Use the existing privately owned OrbStack guest/cached Python image
`python@sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016`.
Actual environment/executable/threading/cgroup pins are in environment.json;
not full kernel/transitive closure. Unique container6501-fd-lifetime-a01-01a0ff52-70ab,
source/root6501-fd-lifetime-source-a01 and output/root6501-fd-lifetime-a01.
Readonly root/source, networknone,0.25CPU,128MiB,pids32, no image pull.
One candidate and one separately implemented raw-only ledger auditor, retries0.
The auditor imports no candidate or ownership implementation. It checks complete
typed event domain, actual native roles, pipe inode/device identities, alias
transfer and current-FD ledger, requested/completed writes, native blocked
witnesses, original D versus replacement R, primary result and final cleanup.

Ordinary two ownership methods and environment-only preflight precede freeze.
They invoke no comparative producer and are excluded from formal evidence.
Retained-data controls are eight predeclared effective mutations: missing row,
float footer count, forged late-close identity, replacement byte as old read,
missing after-reuse witness, second once-owner claim, wrong environment pin and
missing actual cleanup. They require the separately passing baseline first.

## D / stop

PASS_FD_LIFETIME_BOUNDARY_SCOPED requires all6 first rows, all kernel/identity/
causality/cleanup joins, exactly2 integer-only replacement closures,0 one-time
owner replacement closures, both normal positives, original D in every row,
all native threads absent/all FD slots closed, source/environment/count/receipt
consistency and eight effective copied-data refusals. The integer-only hazard
remains unsafe even when the method boundary hypothesis passes.

Missing kernel witness, unexpected callback/read/close, source/environment
mismatch, output occupancy, row exception or cleanup residue is STOP/FAIL and
must retain its first partial raw/log. No retry, replacement or row exclusion.
Each readiness/join boundary has2s cap, candidate15s/audit10s, host30s outer cap,
raw256KiB, expected public package<4MiB. On outer timeout stop only the named
owned container and reconcile terminal state/output, never resend. Disposition
must not be tuned after seeing the result. Subsequent ordinary repair is a new
version with the first evidence intact, not another A01 execution.

## C

Explicit dup2 is an adversarial deterministic schedule, not a natural reuse
frequency sample. The sentinel is a second pipe in the same process, and its
source alias closes after transfer. Device/inode describes retained authored
OS evidence, not hostile-emitter authentication. Exact clocks/latency and
request workload efficiency are not compared. A genuinely single owner with
worker-only closure/control cancellation is another sufficient simple design;
this result does not require the proposed owner wrapper in production.

## U

No arbitrary I/O preemption, EINTR/error-close retry, multiple simultaneous
uncooperative closers, signal-handler allocation, descriptor exhaustion, socket
semantics, macOS/Windows portability, GUI/game/model/input release, currentness,
authority, task effect, throughput or runtime adoption. The bookkeeping is one
shared object for this original lifetime; separate copied owner objects or
ownership reset would not meet its contract. Source/input/image and first
results remain immutable; evidence PR/content votes/current-tree/application
gates are separate. Common fleet deadline unknown and not extended.

| Symbol | 日本語の意味 | SI unit | Definition/type |
|---|---|---|---|
| fd | プロセス内の記述子番号 | 1 | integer >=3; reusable slot, not lifetime identity |
| device/inode | 同じ管のOS識別値 | 1 | nonnegative/positive integer pair recorded by fstat |
| native_tid | 実際の読取スレッド識別子 | 1 | positive OS thread identifier, row/role bound |
| timeout | 観測・終了確認の上限 | s | positive scalar2.0 per boundary, not latency result |
| CPU quota | CPU時間上限 | s/s | actual cpu.max25000/100000=0.25; not measured load |
| memory limit | cgroup上限 | B | actual134217728; not peak memory measurement |

Primary references: Linux man-pages [close(2)](https://man7.org/linux/man-pages/man2/close.2.html)
and [dup(2)](https://man7.org/linux/man-pages/man2/dup.2.html), read2026-10-03.
They document reusable FD numbers, Linux blocked-I/O description references and
atomic dup2 replacement. Local measurements establish only this frozen deck.
