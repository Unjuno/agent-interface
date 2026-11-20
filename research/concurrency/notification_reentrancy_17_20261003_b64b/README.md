# Notification reentrant-consumption counterexample

An arbitrary callable passed to the current app-server notification method can
consume the same selected object using a nested call to that public method.
When it then returns True, the baseline returns A twice and silently deletes
unrelated B. Returning False instead produces RuntimeError: deque mutated during
iteration. This is a directed constructor-free source-method unit construction,
not observed production incidence. Known normal callers use pure comparisons.

| Arm | Predicate | Nested return | Outer result | Remaining |
|---|---|---|---|---|
| Current | pure healthy | none | A | B |
| Current | reentrant True | A | A again | empty: B lost |
| Current | reentrant False | A | RuntimeError | B |
| Outside comparison | pure healthy | none | A | B |
| Outside comparison | reentrant True | A | TimeoutError | B |
| Outside comparison | reentrant False | A | TimeoutError | B |

All six first ordinary cells are retained. Actual threading.Condition default
RLock and live deque were used; no constructor, process factory, native peer,
reader, arbitrary private-queue mutation, mocked clock, sleep or new worker.
Full1025-character rich intent, Japanese/accented meaning, typed marker and local
distinct object identities remain. Timeout0 is a deterministic branch, not a
latency result. Full callback/nested-return traces and first exceptions are saved.

One new CPU construction and a separate independently implemented same-author
saved-only checker each exited0/stderr0 on Linuxarm64/Python3.12.15. PID7 in each
DISTINCT container is namespace-local and not two different voter identities.
Actual cgroups cpu.max25000/100000,memory.max134217728,memory.swap.max0,pids.max32,
networknone/read-onlysource+root/nonroot match. Fourteen frozen input joins and
full process streams/UTC/PIDs reconcile. Twelve effective copied corruptions
are refused and fully retained. Both own containers exited0/Pid0/noOOM; active
own containers0 and own guest stopped. This is implementation independence,
not a nonauthor content vote. Saved UTC/output cap custody is checked separately.

Before any subject execution, main changed via6955 close retirement. First
source-context AssertionError and both old source images remain. Current source
6508B/SHA2290f2f8… and private7137B/SHA98cdae09… share the entire module except
wait_notification. Source wait ASTs equal the historical source/own comparator;
other15 method ASTs current identical. Public preexecution freeze comment's
other14 count is a transcription error: the pinned source-audit complete list
already contains15; no source/decision/measurement changed. Freeze3038B/SHA
df74ca84fed2c66a0e841575bbcccfc5e1be39027dabbf8ef7079165379de956 fixed before run.

The comparator is UNADOPTED:7029's finite retry starvation and changed matching
priority remain, so this result does not supply general recovery or whole-call
guarantees. It is not constructor/reader/journal/wire/Boolean-ID/server-authenticity
or physical cancellation/release/task/control/latency/token/RSS/efficiency proof.
Old7003 four native cells and7029 formal graph are unchanged and not replayed.
No active runtime/test catalogue/workflow/global index change or main send.

Read [SPEC](SPEC.md), [FREEZE](FREEZE.json), [saved audit](raw/AUDIT.json),
[source audit](source-audit.json), [custody](post-run-custody.json) and complete
raw rows/process streams together. Ordinary snapshots end.py.txt and remain
inert. Original metadata/source/raw bytes are preserved without path projection;
binary tar captures use explicit lossless base64 JSON with complete original
byte/hash mappings. SHA256SUMS covers all package images except itself.

Actual worker01a0ff52-b64b / FINAL-v5, claim5969214526, contextcorrection5969254478,
preexecutionfreeze5969265358. GlobalN/commondeadline unknown/unextended. Genuine
fixed-head nonauthor content quorum and later actual-current nonauthor full-tree
coupling/live authority/ownership/sole expected-old history-preserving main CAS
remain separate. Broad computer-control goal ACTIVE.
