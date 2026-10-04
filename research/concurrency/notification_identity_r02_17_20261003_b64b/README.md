# Notification identity repair R02: restore normal scan cost

R01 preserved exact public reentrant consumption, but performed a full queue
membership scan before each snapshot callback. A new ordinary test-before-edit
queue-element-visit budget exposes that cost on pureFalse scans of unchanged
queues. Current source baseline/R01/R02 each visited, for n16/64/256/1024:
- baseline:16/64/256/1024, but retained correctness failures3+deque errors2;
- R01:152/2144/33152/525824, all10 identity controls pass but all4 resource gates fail;
- R02:16/64/256/1024, all15 relevant identity/resource/EOF test methods pass.

CountingDeque yields actual queue rows and counts those yields. This metric is
only queue-element visits: it excludes tuple/set iteration and total allocation,
wall time, latency, CPU/RSS and all model/GUI/task/physical-release costs. No
speed factor or whole-control efficiency is inferred. Pure unchanged queue
visits are linear and match the strongest original baseline, while identity
correctness no longer fails. Full stdout/stderr/command/PID/UTC/hash receipts
are retained. Ordinary regressions only, not a new formal/native allocation.

The constructor initializes one deletion-generation integer before reader start.
Snapshot retains references and a set of their id values. At each next callback,
rebuild live IDs only if a public nested wait consumed a row. Consume only a
currently live exact identity after truth conversion, incrementing generation
under the same Condition. Reader append does not remove a snapshot member and
therefore needs no deletion-generation increment. A retained snapshot keeps
all its referenced identities alive; Python id reuse cannot alias a new row
while that reference remains alive. Predicate always stays under Condition.

Premises: queue removals occur only through wait_notification, immutable object
identity, no private queue mutation or reinsertion of the same consumed object.
Existing public normal callers/reader satisfy this premise. Arbitrary subclass
or private mutation is outside it. Reentrant callback churn may still trigger
quadratic rescans; no general complexity, lockdeadline, arbitrary callback or
finite recursion/whole-call recovery claim. Held predicates still block reader
progress (#7003); outside-lock retry guards from #7029/#7088 are not adopted.
Fourteen other method/module ASTs unchanged. Constructor differs by exactlyone
initialized counter; close/EOF/request behavior remains unchanged, covered by
four existing inert-stream EOF tests with actual short reader threads retired.

H/T/D fixed prospectively in PR7087 comment5969999020 before source revision:
unchanged pureFalse queue visits <=3n+4 across4 declared sizes and all original
identity/EOF controls. R01 first failure PID15671 at2026-10-03T14:16:57UTC; R02
PID15724 at14:17:20UTC exit0/15methods; strongest baseline PID15725 at14:17:21UTC
exit1/3failures+2errors/11methods (four cost subcases pass). Rich Unicode intent
and exact-object identities remain. macOS/Homebrew CPython3.14.5, no native
server/model/GUI/input/release/container/VM call; old formal/native allocations
unchanged and not replayed. Repeated ordinary regression is allowed repair,
not repeat-to-success science. Whole repository/hostedCI remain unverified.

R01 stderr has an original unittest trailing-space line. First publication
whitespace gate failed before ref/send; original package/index/publisher/diff
remain preserved locally. Its new public raw path adds .base64.json and binds
complete original bytes/hash to lossless base64; no raw line was trimmed.
R01 historical archive and parent commit remain immutable/recoverable. R02
changes existing active client and regression file plus this new inert archive.
New content epoch requires fresh nonauthor votes. Original R01 votes, if any
arrive later, cannot approve R02. No current-main applicability certificate or
main sender claim. Local syntax/whitespace/relevant tests/saved evidence checks
are scoped. Reproduce focused suite fromroot:
`PYTHONPATH=research/live_control python3 -B -m unittest discover -s research/live_control -p 'test_*app_server*.py' -v`.

| Symbol | Japanese meaning | SI unit | Type / premise |
|---|---|---|---|
|n|開始時の通知数|1（無次元の個数）|16,64,256,1024; pureFalse unchanged queue|
|v|deque反復が実際に返した要素数|1（無次元の個数）|非負整数; timing/allocation is not included|
|g|成功した公開消費の世代|1（無次元の個数）|初期0、Condition内の成功消費ごとに1増加|

Actualworker01a0ff52-b64b /FINAL-v5 /ordinary17-NOTIFICATION-IDENTITY-R02.
Selectedcurrentmainb46ce67d governing6docs/client equal prior pins; source base
f474970f82d68b6648aac64f99048ad0c2fd5732; no globalresource/apply lease.
Broad computer-control/task-effect/recovery/efficiency goal remains ACTIVE.
