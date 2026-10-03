# Fresh ordinary request-write construction A01, parent59

H: On exact public synchronous client6303B/SHA8ed4e349..., an owned child that
keeps stdin open but does not read can block a large request in stdin.write
before its response timeout deadline exists. The small same-peer control and
healthy large-reader control isolate byte backpressure from timeout/JSON failure.
This is a deliberately stalled inert pipe, not real Codex/model/game behavior.

T: Exactly three fresh sequential actual Windows primary3.12.14 Popen children,
max1 live, journal_path=None. Case/input literals are in INPUT.json: healthy
262144 ASCII X, unread5-character probe, unread262144 ASCII X. Public request
timeout0.05s; fixed parent checkpoint>=0.25s; setup1s/cell3s/raw4MiB cap.
Record actual caller stack/line/source hash/deadline-local presence, write lock,
child/reader/closed state, request result/error/timestamps, wire bytes where
actually read, sideband peer record and final caller/reader/child/parent-pipes.
The owned peer releases via its own private flag; explicit owned terminate/kill
fallback is infrastructure cleanup, never hidden or physical release evidence.

D: Separate frozen saved-only auditor must find healthy exact payload response,
small-unread TimeoutError, large-unread live at source stdin.write/flush48/49
with no request deadline local after checkpoint, and all native endpoint cleanup
complete. Then PASS_NATIVE_REQUEST_WRITE_BEFORE_DEADLINE_WITNESS_SCOPED. Missing
endpoint/control/frame/source, premature phase, unexpected source error or
incomplete cleanup yields STOP/UNCERTAIN; preserve first result, no gate tuning,
same-data native retry, threshold adjustment or runtime repair in this scope.

C: Peer code explicitly never reads in two cells, records reads0, and keeps
both output descriptors open. Small bytes fit only if actually observed to
reach timeout; healthy result proves large JSON can be consumed. Source AST
pins write before deadline; real Python frame prevents guessing the blocked
location from elapsed time. Source has known separate EOF/journal/cache gaps;
those do not explain a live write/no-deadline checkpoint with journal disabled.

U: One sample per cell, no median/worst-case/frequency/payload threshold or total
latency guarantee. Parent performance-clock durations are in ns; child stamps
are separately labelled and never used as a calibrated parent latency axis.
No model/provider/game/GUI/input/GPU/Engine/container/WSLc/formal allocation,
original producer replay, runtime source change, performance or task-effect/
physical release claim. Driver progress/termination is not a server action.

Freeze pins source/driver/peer/input/plan/auditor, selected interpreter/stdlib,
source-site map and exact search/source provenance before child creation.
Planned native wire uses the OS newline because Popen text stdin translates LF;
actual healthy raw bytes must match it exactly. ASCII avoids locale ambiguity.
Primary references: docs.python.org/3.12/library/subprocess.html (text pipes);
learn.microsoft.com/en-us/windows/win32/api/namedpipeapi/nf-namedpipeapi-createpipe
(synchronous anonymous-pipe write blocking). References do not replace native
stage/cleanup observations or prove an end-to-end timeout/latency bound.
Native producer only collects records; an independent auditor decides from
saved bytes without importing client/producer. At most one copied-data audit
mutation set is allowed, not another native exchange. Original audit failure
remains visible if repair is necessary; ordinary repair is versioned.
