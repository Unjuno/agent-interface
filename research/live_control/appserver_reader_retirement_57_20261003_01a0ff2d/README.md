# Reader retirement and late-frame custody repair

After parent exit, `join(timeout)` can time out with the stdout reader still live.
V1 closes the journal anyway: a valid late frame then raises ValueError while
recording and never reaches the cache. V2 adds one actual `is_alive()` check after
join and before journal handling. It raises TimeoutError on incomplete reader
retirement and leaves the journal open. Once the writer releases stdout, the real
reader records and caches its frame; a separate bounded close completes.

This follows b04b's concrete witness5967690163/advisory5967736791. Their original
descendant cells are not replayed. The new ordinary fixture uses an exited harmless
parent and a separately owned harmless writer retaining the same OS pipe. Both
actual Popen handles belong to this driver; no arbitrary descendant-kill claim.
Python's documented join contract requires checking is_alive after timed join:
https://docs.python.org/3.12/library/threading.html#threading.Thread.join

Actual Windows11 build26200 / CPython3.12.10, three necessary commands:

| Stage | Methods | Exit | Result |
| --- | ---: | ---: | --- |
| First RED, V1 source | 3 | 1 | healthy EOF passes; journal ValueError loses frame; no-journal incorrectly returns normally |
| V2 normal | 10 | 0 | prior seven plus three new reader cases pass |
| V2 -O | 10 | 0 | same unchanged definitions pass without assert-dependent production guard |

Full actual argv/source/test/native PID/UTC/exits/raw streams and23 case rows are
retained. Five new-fixture transport invocations in RED and eight per final command
(21 total, max2 simultaneous) are ordinary repair phases, not independent formal
trials. All recorded transport process waits ended0, readers/callers retired, and
driver pipes closed. A late targeted PID-number check found20 absent and one later
pwsh.exe generation; the recorded Python child had already exited. There was no
termination of the unrelated generation. Thread error metadata and original test
traceback are preserved; no separate full reader-exception traceback was captured.

The earlier journal-mutex acquisition, same journal-close exception/finally release,
explicit None mode and all other client methods remain unchanged. The old fake
RetiredReader adds only is_alive()->False; its seven assertions/methods remain
AST-identical. The native protocol selector appends the new reader module exactly
once, retaining the mutex module and all other selections. Both modules were tested
directly in the dedicated directory; the full native/hosted suite was not rerun.

This observes one notification route. Response-cache preservation is unchanged-
source inference; live-reader/already-closed-journal guard ordering is source
reasoning, not an extra native case. None is interface/contract preservation, not
measurement of an unbounded wait. The freeze's monotonic clock is GetTickCount64,
resolution15.625ms; checkpoints/configured phase budgets are not hard wall deadlines.
No guaranteed termination of arbitrary descendants, complete pipe/OS/journal-I/O
deadline, input release, Codex/model/game/GUI/formal task or efficiency result.

Prior105-path V1 tree and its101-file evidence package remain preserved as ancestry;
V1's mutex-only vote is historical and does not approve this changed V2 contract.
Snapshot/helpers end .txt; evidence lives in an inert namespace. Fresh exact V2
content review and actual-current nonauthor combination/live authority/ownership/
requirements/cancellation checks precede any expected-old forward main update.
Votes/application sends remain outside this source tree. Main writes0.
