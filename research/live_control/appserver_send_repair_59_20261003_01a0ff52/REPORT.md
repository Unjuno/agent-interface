# App-server send repair (#59/#57)

The current synchronous client starts its response deadline after buffered stdin write/flush.
Own retained [#6954](https://github.com/Unjuno/agent-interface/pull/6954) first six cells remain unchanged.
This separate ordinary repair integrates exclusive nonblocking descriptor sends into the same client.
It adopts the existing bounded writer's partial-send/quarantine mechanism while preserving arbitrary
previously JSON-serializable record sizes;64KiB limits one syscall, not a message.

Request timeout is now one monotonic budget for write-lock admission, pipe send and response wait.
Notify has an additive timeout parameter (default30 seconds). Invalid/nonfinite/negative/Boolean or
over-lock-range budgets fail before request-ID allocation. Zero is valid but permits no send.
The sole client owns stdin: external buffered writes, flag changes, fd closing/replacement and concurrent
external process mutation violate that ownership contract. JSONL uses UTF-8/LF; default JSON ASCII escaping
preserves serialized text and model input content. Existing Popen text wrappers remain for ownership/close,
but all client sends use the descriptor. This changes the previous Windows TextIO newline translation.

After a pipe-attempt failure, AppServerWriteUncertain retains exact OS-accepted prefix count, total bytes
and original cause, and permanently refuses later request/notify sends before journaling or OS writing.
KeyboardInterrupt/SystemExit keep their identity while also quarantining the connection. No automatic
resend/reset/reconnect. A returned byte count proves pipe acceptance only, never server/action acceptance.
Pre-send lock/budget/serialization/mode/journal failures send no bytes and do not poison the channel.

## H / T / D / C / U

H: this send integration preserves large JSON input and gives a finite uncertain result on owned pipe
pressure without a later append. T: directed repair unit regressions, related fake-model/planner checks,
and one newly frozen two-cell native repaired-runtime construction. D: exact full native wire/params hashes
for healthy262144-byte dummy image input; positive partial count/typed uncertainty before500ms checkpoint,
live peer and reader, and two separately submitted followups with no added OS write under pressure.
Both native children must be deliberately reaped and caller/reader/pipes closed. No native repeat.
C: source timeout was response-only; this is a changed send contract, not a retroactive whole-call promise.
The existing writer's small-record cap cannot simply be adopted for rich model inputs. No new queue,
background writer, retry service or learned controller is introduced. U: serialization and journal I/O,
condition acquisition/arbitrary notification predicates, EOF diagnostic drain, and close are separate bounds.
Scheduling can overshoot the budget; no whole-call hard bound or efficiency estimate is established.

## First outcomes and checks

First RED:13 methods,2 failures/22 errors including subtests; missing new APIs/imports account for many
errors, while shared-budget and invalid-timeout behavior fail directly. Baseline native witness is #6954;
this unit RED is not a second baseline latency experiment. Initial repair13 pass. Timeout validation then
reordered its checks for huge Python integers; final directed suite15 pass in the related run and15 under-O.
Related38 methods:36 pass/2 Windows-path expectation failures. An isolated unchanged e527 base export
reproduces those exact two failures (actual child exit1), without importing the modified client. Tests and
planner sources remain unchanged. Whole related suite is FAIL with a classified pre-existing expectation.
The15 new methods are registered once in the existing shared protocol entry; the full entry and hosted CI
were not executed or claimed PASS. Root has no configured Python linter; changed Python AST/import/unit
and publication whitespace/navigation checks are used.

Native plan2a26ccf7768f3a52ac3c17528952b07c199564134fa0dde4ea53049d96b4d9e0 frozen before the only
two-cell invocation. Actual macOS27.0.1/arm64 Python3.12.13, stdlib/default Popen text=True/bufsize1,
one owned inert peer at a time; dummy image text, no image decode/model/provider/GUI/input. Transparent
OS-write observation records each actual return/error and suffix digest independently of the client count.
Healthy262323 bytes fully received (6 attempts,0.001951250s); pressure65536/524467 bytes accepted before
TimeoutError→AppServerWriteUncertain (2 attempts,0.055093791s for configured0.05s budget). Both fresh
notify/request followups refuse with0/0 and attempt count2→2. These are single descriptive durations,
with unknown load and no general latency/resource/correct-task claim. Native children exit-15 explicitly;
base client.close leaves all3 pipe wrappers open, and this driver then closes them. Owned peer/driver PIDs
are later absent. No cleanup/release repair is inferred from those driver actions.

Saved-data v1 exits1 before materializing copied controls because Python True==1 makes the copy generator
misclassify a type-changing mutation as ineffective. Original source/error retained. Post-result v2 only
changes mutation-effectiveness comparison to canonical JSON and separate output paths; original2 rows
and all12 altered copies are checked. Original native data/source/plan/gates unchanged; native replays0.
This is scoped sensitivity and byte/count/lifecycle custody, not complete adversarial producer authenticity.

## Eligibility and adoption boundary

Unix pipes use select; Windows select only supports sockets, so the Windows branch sleeps up to10ms
between nonblocking attempts. [Python3.12 os.set_blocking](https://docs.python.org/3.12/library/os.html#os.set_blocking)
documents Windows pipe support beginning at3.12; [select documentation](https://docs.python.org/3.12/library/select.html)
documents that socket restriction. Earlier/unsupported pipe modes fail before send. Actual Windows3.12+
pipe, partial/zero-write behavior, LF interoperability and older-runtime compatibility disposition remain
unverified: **HOLD cross-platform runtime adoption pending independent Windows native qualification**.
Linux-native execution of this repair was not performed; only the earlier Linux writer mechanism is reused.
EOF diagnostic #6953, Boolean-ID #6952, startup b04b and journal-close be6f remain their owners' separate
source lanes; this PR does not apply them. Any current-tree combination must preserve their changes and
perform the appropriate negative checks before adoption.

Fixed prospective genuine nonauthor agreement, actual-current-tree confirmation, live requirements and
sole-owner expected-old main update are still required. No main send, no lease or reset/replay is held.
Actual task effect, environment-change recovery, per-key release, full model/game efficiency and whole
computer-control completion remain unestablished.

## Custody and safe archive

All archive Python is .py.txt or .txt, unimported by runtime/discovery/workflows. Active changes are only
the existing client, one new unit module, one shared protocol registration and one existing index row.
The prospective native source/client/test/peer/driver pins are retained. First GREEN source pair is a
post-result reconstruction verified against its earlier captured hashes, explicitly not pre-command
file copies. First check wrapper itself was not prospectively source-pinned. Later checks capture source
bytes, argv, PID and exit. Actual peer argv/PID/default kwargs and final observed exit are captured;
there is no separately saved peer stdout/stderr byte stream or precise child exit instant.
Public snapshots replace only owned absolute workspace paths; private originals remain retained.
MANIFEST.json records original and public lengths/hashes and distinguishes byte-identical files from
path projections. Projected helper snapshots are inert relocation examples, not the exact executed images.
Exact active/runtime source snapshots, native wire bytes and source hashes retain their original images.
Do not replay the native producer from this historical archive.

Publication first whitespace exit2 and sparse navigation exit1 are preserved in PUBLICATION_STOP.md. After exact six-doc restore and single-frozen-stderr trailing-space attribute, staged whitespace exit0, workspace156 exit0 and navigation26/1641 exit0. The newly added live-control row is separately verified against its staged target. Active tests/source were not changed by publication repair. Apple M1 Max/64GiB was observed in a later host sysctl snapshot, not an original load measurement.
