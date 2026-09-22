# WAL retention under coherent read snapshots — #531 / b72c successor

## Result and chronology

**PASS_WAL_SNAPSHOT_RETENTION_BOUNDARY_SCOPED.** One locally prospectively frozen
allocation `wal-snapshot-retention-531-d90e-20260922-01`, two immutable serial
batches, six fresh cases, 768 post-initialization private-model write transactions.
No case rerun, replacement, exclusion, threshold change or post-freeze source
change. Separate raw-only audit: 2,479 row/file/protocol checks, errors=[],
12/12 real semantic/provenance mutations rejected. Twelve unit tests passed.
All12 actor exits and both observed batch exits are0; all14 recorded PIDs absent
on later /proc check. Actual waits, not absence alone, establish successful exit.

**Publication is LOCAL_ONLY / HOLD_GITHUB_WRITE_ACTION_UNAVAILABLE.** The current
GitHub connector exposes48 read actions and no create/comment/PR/merge/delete
action. The installed-provider search found the same connector; local gh/docker
CLIs are absent. No remote write, Issue creation, branch push, PR, main mutation,
CI result or branch deletion is claimed. No blocked action was bypassed. A later
publication must be labelled retrospective, not public preregistration. The
experiment itself was fixed before execution locally, with its freeze digest
shown in the conversation before the first formal command.

Intake main2308b8301d69b7089a2e0636486736ed59b61537. Last read main
33e86e997d02b769af17a3f03f6035c68927da6e, updated by other work. The new namespace
was absent at the pinned intake main. No whole-repository checkout/CI was run.
Original #531 remains closed with its scoped result unchanged. The source and
scope boundary are not a production SQLite defect or a new database theorem.

## Question and controlled difference

The earlier b72c allocation established why related state fields should be read
in one coherent transaction. It did not measure how long such a transaction may
be held while subsequent accepted work continues. The new question is whether
logical history capacity2 also bounds persistent WAL extent.

HELD_TX reads the complete initial view inside one read transaction and retains
that transaction. COPY_RELEASE reads the SAME complete initial view inside one
transaction, copies its values into memory, then immediately commits the read
transaction. Both return the same historical inner payload after writer work.
BEGIN_ONLY is an additional exposure control: BEGIN without a SELECT does not
capture that initial view and subsequently reads the final view. It is NOT a
semantically equivalent replacement for an initial-state observation.

Only reader lifetime/exposure differs. Writer source, schema,128 accepted new
intents, checkpoint configuration and barrier ordering are identical. Complete
#531 model.py is unchanged: Git blob24329aaedf166b98a5babf5cfb9c61af7c6f40f0;
SHA25625b0f18cd9d5fcfd69608810f0ea8f4cde60b076baa637f5dad5d4f1143507a7.
The new actor persists model state; it is not a full production runtime.

## Retained measurements

Apparent WAL file extent in bytes, after each stated number of post-initialization
commits. Each entry is the median of2 fresh cases; both cases have exactly the
same value, so each observed range is the single displayed value.

|Reader mode|After8 writes|After32 writes|After128 writes|Pre-release TRUNCATE busy|After release and TRUNCATE|
|---|---:|---:|---:|---:|---:|
|HELD_TX|65,952|263,712|1,054,752|1 in2/2|0 bytes in2/2|
|COPY_RELEASE|8,272|8,272|8,272|0 in2/2|0 bytes in2/2|
|BEGIN_ONLY|8,272|8,272|8,272|0 in2/2|0 bytes in2/2|

Every committed writer view retains two history rows. At completion all modes
have generation132, retired-through129, history sequences130/131. Every one of
the768 fresh transitions is APPLIED by the unchanged model. Initial construction
of seq1..3 is separate from these768 updates. No dispatch/model/GUI action occurs;
private fixture database mutations are real, not claimed absent.

The retained-view policies both return generation4, retired-through1 and history
2/3. COPY_RELEASE does not improve freshness: it preserves an explicitly
historical response while ending the database read transaction. It does not
turn that response into current input authority.

WAL files here are observed apparent extents (`st_size`), NOT physical storage
consumption, total bytes written, RAM, tokens or a latency benchmark. Original
`st_blocks *512` values are diagnostic only. This finite workload does not prove
an unconditional bound under unlimited writes or arbitrary readers.

## Successful checkpoint call is not complete reclamation

At8/32/128 writes, HELD_TX returns PASSIVE triples `[0,16,0]`, `[0,64,0]`,
`[0,256,0]`. The first zero is the call's non-busy status; the third field shows
that none of those frames was checkpointed. It must not be exposed as a generic
"fully flushed" or "storage reclaimed" receipt. Pre-release TRUNCATE returns
`[1,256,0]` and leaves the WAL intact.

The other two modes return `[0,2,2]` at each measured stage and TRUNCATE succeeds
before release. After explicitly releasing the reader, all modes return
`[0,0,0]` from TRUNCATE and the apparent WAL extent is zero.

All modes use `wal_autocheckpoint=1` page and `journal_size_limit=16384` bytes.
The held case exceeds that configured limit despite successful writer commits
and automatic/PASSIVE checkpoint attempts. `journal_size_limit` is not a hard
live-WAL quota. This interpretation follows the documented checkpoint/reset
semantics; no SQLite misbehavior is alleged.

## H / T / D / C / U

|Field|Frozen meaning and outcome|
|---|---|
|H|An old active snapshot can prevent WAL reclamation even with two retained rows. Ending the transaction after coherent copying preserves the same historical response and permits reclamation in the declared single-reader fixture. Supported.|
|T|3 modes x2 fresh cases,128 writer commits each; two3-case batches; separate writer/reader processes; explicit barriers; WAL/FULL/page4096/autocheckpoint1/journal limit16384/busy timeout0/read_uncommitted OFF.|
|D|Complete6/768/12-actor/2-batch accounting; held extent increases, incomplete PASSIVE and busy TRUNCATE; copied/begin-only extents below frozen65536 fixture bound; release permits truncation; source/raw audit and mutations pass. No acceptance gate was relaxed.|
|C|Known SQLite mechanism, with a new application-adapter workload. Writer rewrites two small table pages per update here; other schemas/large transactions/multiple readers can differ. The copy policy is appropriate only when historical evidence suffices; it is not latest-state admission.|
|U|No power loss, multiple writers/readers, native GUI/model utility, performance or cost gain, hard disk/RAM bound, storage-device durability, production adoption or global ROADMAP completion. Six directed cases are not a failure-rate estimate. No calibrated u_c or coverage factor k is invented.|

## Implementation and measurement assumptions

Supplied Linux6.18.44 x86_64 execution container, CPython3.13.5, SQLite3.46.1.
Guest identifies AMD EPYC9V74; CPU affinity/frequency not pinned or isolated.
No Docker/OrbStack CLI or engine-image attestation is available; no such
replication or enforced network-none guarantee is claimed. Experimental code
makes no network calls, installs no packages and touches only fresh private
files. ENVIRONMENT.json records Python, SQLite compile options, library/binary
hashes, CPU MHz snapshots, affinity and clock implementations.

Writer commit windows end before raw-file copies. Both actors wait at explicit
pipe barriers while the main DB/WAL/SHM bytes are copied. These are labelled
quiescent byte copies under cooperative actors, not crash-atomic live backups.
The independent auditor ignores copied SHM and restores DB+WAL in a fresh private
directory for read-only SQLite reconstruction. It never opens the retained
originals writable or uses immutable=1 to silently ignore their WAL.

## Variables and unit check

|Symbol|Meaning|SI unit / storage notation|Definition / domain|Type|
|---|---|---|---|---|
|B|Apparent WAL extent|1; measured in bytes|Nonnegative st_size at quiescent capture|integer scalar|
|P|Page payload per WAL frame|1; bytes|4096 in this allocation|integer scalar|
|H|WAL file header length|1; bytes|32 for nonempty observed WAL|integer scalar|
|F|Per-frame header length|1; bytes|24 per SQLite WAL format|integer scalar|
|N|Valid committed frames in current WAL cycle|1|Raw checksummed frame prefix; not inferred solely from file extent|integer scalar|
|w|New accepted commits after initialization|1|8,32,128 measured formal milestones|integer scalar|
|c|Retained history capacity|1|2 committed rows|integer scalar|
|t|Monotonic diagnostic timestamp|s; stored in ns|Same-container clock, ordered only|integer scalar|

For this observed no-unused-tail WAL, the file-format accounting is
`B = H + N * (F + P)`. Dimensions are bytes + dimensionless-count times bytes.
At the held128-write sample, N=256 and B=32+256*(24+4096)=1,054,752 bytes.
In the other modes the observed current cycle has N=2 and B=8,272 bytes.
The raw-only parser verifies magic, version, page size, salts, every chained
header/frame checksum and last commit marker. Extent is not generally identical
to active frames: the parser explicitly handles a tail from an older salt cycle.
This accounting is not a throughput or real-time claim.

## Conditional reasoning, from assumptions to interpretation

1. A read transaction that has selected a state must preserve its observed
   version while it is open; our HELD_TX reader actually selects and later
   rereads the initial values, rather than merely holding a connection.
2. The writer performs the same128 valid committed transitions in each arm.
   Their final views all agree. Thus held-reader growth is not explained by
   greater logical history or additional accepted operations in that arm.
3. The held reader constrains checkpoint progress. Every measured PASSIVE
   response has a zero completion count; retained WAL checksums and frame counts
   independently reconcile those response fields and the growing extent.
4. COPY_RELEASE preserves the same serialized inner view but ends the read
   transaction before writer work. That removes this reader's database
   snapshot requirement. Its fully checkpointed/reused WAL and successful
   TRUNCATE are observed, not inferred from a call's first status field.
5. BEGIN_ONLY selects no initial data and behaves like the released control
   for reclamation, but it obtains a later state. This separates BEGIN from a
   pinned read snapshot and prevents an "open connection alone" explanation.
6. Ending the held transaction permits the same writer's TRUNCATE to succeed.
   No extra write workload, increased timeout, another model call or changed
   journal setting was needed. This is the declared final phase, not a retry
   replacing the failed pre-release observation.
7. Therefore a logical retention cap plus coherent acquisition does not by
   itself supply a resource-lifetime bound. A possible integration rule is to
   copy coherent bounded evidence, end its read transaction, and label the copy
   historical. Applications that need a later state require a new explicitly
   fresh read/admission boundary. The experiment does not certify that broader
   integration or arbitrary background cleanup.

## Audit, preserved evidence and exclusions

Frozen12 files unchanged. Original174 formal files remain byte-identical before
and after audit. Twelve units passed; all12 mutation controls reject dropped or
duplicate cases, changed mode/state/extent, false completion/PASSIVE/TRUNCATE,
Boolean exit, missing exit, claimed open copy transaction, and fabricated
BEGIN-only capture. The test suite also rejects a checksummed WAL payload
mutation. These finite controls do not prove arbitrary auditor soundness.
Audit independence is separate implementation/process by the same author, not
external human review or a distinct trust root.

One excluded3-case construction used only2/4-write milestones. It completed once,
exit0,431 raw checks and12 rejected mutations. No construction or formal failure
was observed. Initial unexecuted draft pipe buffering was changed before the
construction. The final source freeze was after construction and before formal.

The b72c source/raw archive was restored into a separate directory and re-audited
without launching any old experiment. All918 old files remained unchanged;
its output equals original AUDIT SHA256
48930301b596129cb76c842c48f824509974ffe4aa3618c9d3ca9c3db7eaf2b9.
Original b72c archive SHA256
9439064827c483529e86260149bfedefc38f3e6201dfaed70ce1544c129a63c9
remains conversation-hosted; this new bundle includes the read-only revalidation
receipt, not a claim of earlier complete GitHub publication.

|Current artifact|SHA256|
|---|---|
|FREEZE.json|286a2f38a0366bbee7a549f2e52af75ae21e0ab8d8ce3b747b9e03bf5cbea38a|
|AUDIT.json|84c37034617bd75c4c66dced1c78f90f02d4ae3f3c60d8473480c66e30b071b6|

## Handoff and remaining roadmap

Readable source/report plus a lossless evidence capsule and an additive patch
are delivery artifacts, not a claimed merge. A future publication worker must
preserve local-freeze chronology and the old results, inspect then-current
Issue/PR ownership and the exact target subtree, publish retrospectively under
a genuinely distinct resource-bound successor, and verify current-head review,
checks and main bytes before claiming integration. Do not rerun this allocation
merely to make publication easier. No branch is deleted based on Issue state.

Parallel #4063 examines freshness of repeated outcome polls, not storage
reclamation or equivalent historical copying. #4037 examines concurrent intent
acceptance during compaction; #3929 examines split writer publication. Their
ownership, source and outcomes are unchanged. Bounded searches cannot establish
absence of unpushed work.

Concrete transfer: database transaction lifetime belongs in the resource budget
of bounded local mechanisms. Separate history row capacity, snapshot lifetime,
WAL extent, checkpoint completion, historical content and current authority.
The broad model-fixed task/latency/token comparison and global ROADMAP remain
unfinished. This work changes no production default or user-facing runtime.

## Read-only reproduction

After verifying and extracting the provided complete bundle into a fresh path:

```sh
python -B audit.py --controls
python -B test_contract.py
```

Never run consumed `execute.py --mode formal` / `run.py` allocations. The
publication unpacker only verifies/extracts files and never executes research
code. Fresh unpacking and a byte-identical offline audit are delivery checks,
not new scientific trials.

## Primary documentation

SQLite WAL/checkpoint starvation: https://www.sqlite.org/wal.html
PRAGMA semantics: https://www.sqlite.org/pragma.html
WAL checksum/frame format: https://www.sqlite.org/fileformat2.html
Checkpoint API: https://www.sqlite.org/c3ref/wal_checkpoint_v2.html
These primary sources motivate and delimit the known mechanism; they do not
substitute for the retained local measurements.
