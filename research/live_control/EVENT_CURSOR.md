# Event-boundary reads over a retained output prefix

`event_cursor.py` is a private observation-only reader primitive. A caller supplies
its last sequence, desired boundary events, timeout and maximum batch size. The
read returns every intervening record through the first requested boundary;
later records remain available. Reading neither consumes records nor acknowledges
interrupt resolution, grants authority, or renews a lease. Independent cursors
can replay retained records. Records are JSON-copied on append/read.

Retention is bounded by record count (default 256), not bytes. If a cursor falls
behind eviction the result is explicit `gap`, with oldest/latest sequence; it
never silently advances the caller. This does not guarantee indefinite interrupt
retention. Timeout, closed stream, matched boundary and batch limit are distinct.
Closed streams drain remaining records. Conditions wake readers on append/close;
there is no sleep-poll loop inside the primitive.

`probe_live_event_cursor.py` connects a subprocess stdout reader to this cursor
and drives the same two scripted Calc tasks through frozen interactive_v23.
The effect read ends before the subsequent independent-evaluation read. Independent
saved-file checks remain successful/unsaved as expected.

| Case | Early emit to reader return | Early return to final return |
|---|---:|---:|
| Save | 6.371 ms | 13.975 ms |
| Unsaved | 5.750 ms | 3010.867 ms |

These are local supervisor timestamps on the same monotonic clock. They are not
model receipt timestamps. `audit_event_cursor.py` verifies the concatenated read
batches equal the entire stdout prefix through final evaluation (25/11 records),
with no omitted intervening event. Controls cover immutable copies, replay,
interrupt inclusion, batch limits, timeout, explicit overflow gap, close/drain,
append-after-close rejection and future-cursor rejection.

Results and retained reads: `results/live-event-cursor-01`; audit:
`results/event-cursor-audit.json`. Source hash for the cursor is recorded separately
from the existing runtime and probe manifests.

This is not yet an assistant-callable transport or a changed Codex tool. The
supervisor runs within one exec invocation, so this turn does not demonstrate
earlier model wakeup or reduced assistant wall time. Next expose one bounded read
per caller invocation through a local session transport and use it directly,
including slow reader/disconnect tests. Keep cursor gaps and EOF visible; never
treat a transport timeout as application termination. No default promotion,
cross-domain performance claim or freeze credit.
