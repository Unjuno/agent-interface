# Explicit transport close stops logical waiters before reader retirement

At main base `acfc856eaa1dc57c10bea2e06c5d9cc6278d9221`, explicit close set
`_closing` but did not notify condition waiters. Request/notification waits only
observed `_closed`, which the receiver sets after its read loop exits. Holding
the receive journal therefore kept the receiver and a 90-second planner wait
alive after process termination and reader-close timeout. The first RED records
this with owned pipes and the actual V2 client/planner plus a local Python peer.

## Adopted boundary

Close commits `_closing` under the condition/publication lock and immediately
notifies waiters before attempting process/reader/stream/journal retirement.
Request and notification waits reject explicit closing with `AppServerError`
and an unverified-retirement diagnostic. Explicit close does not consume a queued
notification or grant a queued response after its stop point. Passive stdout EOF
still permits retained matching notifications, preserving the existing contract.

Notification predicates execute under the condition. The code rechecks closing
after a predicate so a reentrant close cannot resume publication. Review first
found the flag was set outside that lock: a gated predicate could consume a row
after `_closing` became visible. Two deterministic RED controls reproduce that
race and reentrancy before the correction. A cached publication that completes
before close acquires the lock remains ordered before the close stop point.

This is a logical session fence, not a successful-close, neutral-input, process
recovery or task-success certificate. Close still raises its existing reader
timeout while the journal remains held; no success status replaces it. After
the fixture releases its own journal gate, owned cleanup reaps the peer, retires
both threads and closes all streams. Gate release is test cleanup, not automatic
task recovery.

## Conditions and retained raw

Five new methods cover pending requests and notifications (two fault cells),
retained-notification refusal, serialized cached publication, predicate reentry,
and actual client/planner with real Python subprocess/stdio pipes. The peer is
finite synthetic JSONL code embedded in the test; it is not installed Codex,
an external provider or a model. It replies to thread/turn start and emits one
fixture pulse after a test-owned file gate. There is no GUI or OS input.

While receive-side journal ownership is held, explicit `close(timeout=.03)`
terminates the peer but reports incomplete reader retirement. The local planner
wait exits with `AppServerError` while `_closed=false`, receiver alive and journal
still held. The .2-second joins are finite test observations, not a worst-case
latency bound or performance sample. The final JSON row records peer return code,
thread/stream retirement and exact journal bytes as base64. Each mode's
`owned-peer-journal.jsonl` is decoded byte-for-byte from that retained log row.

First affected checks also exposed four errors from a preexisting partial
`__new__` journal fixture lacking a condition; adding the constructor's condition
restores it without weakening journal-lock/error assertions. The first green
and affected failures remain. The initial broad run passed before review's
publication controls and is retained as intermediate evidence, not qualification
of the final correction. No historical producer or consumed allocation reran.

Final clean code `e9fa391b024f9ee27d1b571dc4fb9fa4ee8370de`: normal and
optimized Python each pass 51 isolated modules / 376 methods, zero failures,
11 skips (365 executed). Skips are the deliberate real-Codex handshake and ten
host-inapplicable POSIX conditions; they are not qualified by this Windows run.
Bounded read-only review passes all five final focused methods in both modes.
The local entry now includes the eight affected transport modules in addition
to the previously qualified control modules. Commands:
`../check_map01_control_regressions.py --output-dir <fresh path>`, adding
`--optimized` for the second mode. Source/status summaries and all logs are kept
under `normal/`, `optimized/`, `intermediate-normal/`; `MANIFEST.json` hashes this
packet. Host: Windows, Python 3.13.14, python-xlib 0.33, Pillow 12.2.0, MCP 1.30.0,
openpyxl 3.1.5. Optional remote CI and installed-App-Server behavior are unverified.

## Remaining gates

Arbitrary condition holders/predicates, journal/stream filesystem operations,
process termination, close itself, native I/O, scheduler/GIL and physical release
are not proven hard-time bounded. This Windows owned-peer fixture does not
qualify POSIX descendants, WSL interoperability, installed App Server semantics,
or every failure exit. Fatal controller retirement can still block inside close
itself even though its planner waiter has stopped. New input/replacement authority,
window incarnation, independent task effect, finite task recovery and matched
economics remain open in #17/#59/#57. No real display, provider/model, game, WSL or
container allocation was launched.
