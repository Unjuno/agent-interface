# Reader-retirement source/contract analysis

This is static assistance within author session01a0ff2d, not a FINAL-v5 vote, independent application certificate, peer native replay, or native execution of the author's repaired client. Production/test ownership remains with the parent; other startup, stderr EOF, write-deadline and encoding scopes are untouched.

The inspected owned v1 repair is `work/repairs/appserver-journal-close-01/codex_app_server_client_v2.py`:6513B/SHA256 `464c770e357b664c35866e271740380307bfcd52dbaa8573e258d5600c006531`. Its test image is9567B/SHA256 `c6598d088225e50d428448390f76a30e2e146a5c0b82c93c115db97e796bdc98`. Exact snapshots are retained beside this analysis. The proposed separate close-02 path was absent when checked; no uncreated source/test was reviewed.

## Defect and smallest repair

The client's process-retirement block and `self._reader.join(timeout=timeout)` are AST-identical to the peer's exact baseline6303B source, SHA256 `8ed4e3496ef8154d3c4573fb1386efe6e036292a3809e43aa37fc22aecc5b42b`. `_read` is also AST-identical. The peer comparator6407B/SHA256 `ea383c9926dd39db56ada5881d318ae6a6d9fe1897b3357cf21ae4ff57c7b129` is exactly the original byte image plus one two-line reader guard after the join.

`Thread.join` returns None both on retirement and timeout; `is_alive()` distinguishes them. None timeout waits until retirement. These are explicit Python contracts: https://docs.python.org/3.12/library/threading.html#threading.Thread.join .

The smallest repair places this guard immediately after the join, before and outside the journal condition:

```python
if self._reader.is_alive():
    raise TimeoutError("app-server reader close timed out")
```

This ordering matters: a live reader must report incomplete retirement for an open journal, no journal, and an already-closed journal. It must not proceed to lock acquisition or journal close merely because the journal condition is false. It must not set `_closed`, clear caches, close transport pipes, or manufacture retirement. In a genuine reader thread, False after join establishes that its run has ended; a thread object cannot be restarted. An exit immediately after a True observation can conservatively produce a TimeoutError, with a later explicit close able to complete.

An exited parent does not imply stdout EOF: an owned descendant can retain the writer. The current finite join can return with a live reader, then close an unheld journal. `_read` invokes `_record('received', message)` **before** populating responses/notifications. A resulting closed-journal ValueError therefore loses both journal and cache delivery. The guard preserves the open journal while incomplete, permitting later released input to be recorded and cached by the existing reader before a separate close completes. It does not change parsing, error handling, queue semantics, or the response/notification update order.

## Preserved and changed close contract

| Condition | Required result |
|---|---|
| Finite join leaves reader alive | Raise reader TimeoutError before touching journal lock or close; preserve journal/cache state. |
| No journal or already-closed journal, reader alive | Same reader TimeoutError; retirement status does not depend on journaling. |
| Reader retired, open journal, lock contended | Preserve existing finite journal TimeoutError and open journal; do not release the holder's lock. |
| Reader retired, journal close raises | Preserve the same exception instance and release the acquired journal lock in finally. |
| Reader retired, no/already-closed journal | Return normally without acquiring the journal lock. |
| close(timeout=None) | Keep process waits and reader join unlimited; after retirement, keep journal-lock timeout=-1 unlimited. The new guard does not insert a finite budget. |

The existing `RetiredReader` double needs `is_alive()` returning False. Missing that method would be a fixture defect, not a production regression. Existing None-timeout tests must still observe join(None). Optional stateful test doubles can establish that journal closure occurs only after the reader's retired state, without claiming physical wait-time measurements.

The timeout remains a per-phase argument, reused for process wait, kill wait, join and journal acquisition. Neither existing repair nor the new guard promises a total close duration no greater than timeout. The change does not terminate arbitrary descendants, close the three process pipe handles, propagate prior reader-thread exceptions to close, drain stderr, or prevent concurrent post-close sends. Those remain separate contracts/owners. A normal return after the repair proves observed reader retirement and any applicable journal closure; it does not prove all-client correctness or descendant/resource retirement.

## Minimum meaningful regression criteria

1. A controllable live-reader double records join's exact finite timeout and stays alive; assert exact reader TimeoutError before any lock acquisition/journal-close call. Parameterize open journal, absent journal and already-closed journal. This catches misplaced conditional-only guards.
2. Preserve existing retired-reader journal mutex refusal, held-lock custody, same journal-close exception identity/finally release, and healthy no-journal/already-closed lock-skip controls. These catch scope expansion damaging the original6955 repair.
3. Preserve explicit None: retired reader receives join(None), open journal closes through unlimited acquire(-1), and no-journal returns without lock access. A gate-based Python-only reader test can test unbounded wait/release ordering if needed; no peer helper or native-cell replay is required.
4. A controlled late valid message can exercise the existing `_read` against an open journal after the refusal, proving journal and response/notification cache preservation, then retired-reader later-close success. Include both response-ID and notification paths if the test claims both. Distinguish journal bytes and typed cached payloads from a mere close-call count.

The finite state/error-order checks decide this minimal guard composition. Peer native rows provide the inherited boundary trigger, not native execution evidence for the author's source. Any new ordinary native confirmation needs its own source/conditions/outcomes and must not reuse the peer's cells or original6955 children as patched-source measurements.

## Evidence custody

The58-file public envelope was decoded **as data only**, under `peer-data/`. Gzip24144B/SHA256 `4a3b2d239995d1f4981ec6ce7ba9cb55bafbc404e53aa722be9066bd176b6e27`; payload126551B/SHA256 `f78eb859e84247c0165d3b8d6740f1361f2efa9c162c23104379a197c45adbd0`. Every public UTF-8 file length/SHA256 matches;35 identity files also match declared original identity, while23 projected private original images are not independently authenticated. No decoded helper/checker/client was imported or executed.

Literal raw-record reads preserve four OBSERVED cells and the first comparator JSONDecodeError STOP. The original held row records normal return/live reader/closed journal/ValueError/no late cache; the comparator held row records reader TimeoutError/live reader/open journal/late notification/no reader error. These remain the peer's attributed native observations. This analysis did not rerun their saved checker, validate all native receipt semantics, or remeasure any native cell. The first invalid parent's unretained exit code remains unknown.

A preview command encountered a cp932 UnicodeEncodeError while printing a public comment; input bytes were unchanged and the inspection continued with ASCII JSON rendering. That inspection error is retained in `inspection-first-error.txt`. All native first outcomes remain in the decoded original public package. No GitHub write, Git mutation, root source/test edit, model/UI/formal allocation, or native subject-process creation occurred.
