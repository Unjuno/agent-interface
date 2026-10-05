# Notification R03: examine arrivals before waiting

When a notification predicate enters another public wait, the Condition can be
released while another public consumer removes the selected object and the
reader appends a new eligible object. R02 preserves identity custody but can
enter Condition.wait before examining the already queued new object. Outside
worker34fb public construction5970621168 demonstrates this with actual public
nested marker wait and actual source reader; original source/raw and all prior
R01/R02 outcomes remain unchanged. This revision adds three lines after the
expired-deadline check: identify snapshot members, detect an unseen queued
identity, and rescan before closed-state refusal or sleep.

Source SHA c23d93cef334c0f501da38e80638077f540eb68eb0457131aabf68128e00811c.
All15 class methods other than wait_notification, including constructor,
reader, request and close, are AST-identical to R02. Initial queued-match
priority over zero timeout is retained. The deadline check precedes rescan;
this provides no bound on a predicate's own runtime or nested call duration.
Queue removals must occur only through public wait; consumed objects must not
be privately reinserted. Snapshots retain references, preventing id reuse for
the objects whose identities are tested. Callback evaluation remains under
the same Condition. Arbitrary reentry/churn may cause repeated scans.

New ordinary repair regression17 methods, PID57500, macOS Homebrew Python3.14.5,
2026-10-03T15:46:13.324655–15:46:13.440578UTC, exit0. Two new real Condition
cases (reader open/EOF after marker) use public old consumer, public nested
marker wait, actual _read and three short owned threads each. Both return
old/marker/new once, consumption count3, empty queue, callback visits old/new,
only nested callback wait, and completion before cleanup notify. All threads
retired. Remaining11 identity/resource and4EOF definitions are unchanged.
No client constructor, real server/model/GUI/physical input/VM/formal or peer
producer replay. EOF may race outer consumption; no delay factor is inferred.

Separate unchanged private boundary definition SHA1d278aa3917e3d90d7de719ab341bbaa6a601daf426ade3cebc46bf00b597ed6
passes4 deterministic methods for R03 PID55967 (15:39:32.686852–.767886UTC).
R02 PID55965 fails the2 new-match/churn cases by reaching intentional wait;
expiry and unchanged queue cases pass. At positive remaining time, stable
pure-false n0/16/64/256/1024 queues make one wait and at most2n counted deque
visits; prior zero-time11-case resource test yields n visits. This measures
deque yields only, excluding tuple/set iteration, allocations, CPU/RSS/wall
time and total task/control resources. Fake-clock ongoing append stops after
snapshot lengths1+2+4 at its deadline, retaining all8 rows. Direct append and
Condition double are schedule proxies, separately qualified from real threads.
No general complexity, wall-time recovery or economic claim.

Earlier private serialized16-method result and first wrong _record stub
failures are preserved, not relabelled. Their actual _read inside callback
was a schedule projection. The stronger public reentry evidence remains a
separate peer result; own saved-only checker verifies its34 member packet,
published/original stream projection joins, exact R02 source, ordered custody
and retirement and rejects5 coherent semantic changes. No peer helper executed.
Peer packet is losslessly retained as inert base64 JSON; private provenance
remains unauthenticated. Full raw byte hashes, recipes and PID/UTC receipts
are retained. All old17 R01 and27 R02 inert Git images remain exact.

Observed current main ed9d4d3d9d5008571128baacc7edfca04cfc847b has the same
six governing documents and baseline client as the original source base
f474970f82d68b6648aac64f99048ad0c2fd5732. This is a content proposal, not a
certificate for that or any future main. Current native protocol catalogue
does not enumerate these identity/arrival modules; it is unchanged. Explicit
focused17 command is recorded in the ordinary receipt. No claim of automatic
whole-suite/native coverage. Current workflow headers checked: native-mcp-v1
and full-golden-ipc-source-integrity match live_control paths; optional CI
is not awaited, commit includes [skip ci], no workflow/manual/tag trigger edit.
Archives contain data-only .py.txt or lossless base64, no test discovery entry.

Supersedes public R02 content digest f045cbde2dd2cb123f24c6eb588b8bb3d9b429edd84c995a8e8639ce88ccce56.
Fresh epoch notification-identity-r03-arrival-before-votes keeps the same
existing genuine nonauthors b04b/d447/e0cc, threshold2, explicit acceptance
and scoped same-descriptor votes. No old vote transfers. Shared GH login is
not another worker or a mandatory platform review. Later actual-current
nonauthor full-tree/raw-ordered-parent/dependency applicability, sole fresh
owner/cancellation/rules and forward expected-old main sender are separate.
main sends0. Common N/deadline unknown; no new worker or deadline invented.

| Symbol | Japanese meaning | SI unit | Type / scope |
|---|---|---|---|
|n|待機前の通知数|1（無次元の個数）|非負整数、ここでは0/16/64/256/1024|
|v|dequeが返した要素数|1（無次元の個数）|非負整数、他の反復や割当・時間を除外|

Author01a0ff52-b64b / FINAL-v5. Whole repository, real server, whole-call
recovery, physical release/task effect and overall efficiency remain unproved.
Broad goal ACTIVE.
