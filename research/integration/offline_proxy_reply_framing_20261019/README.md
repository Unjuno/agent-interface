# Offline X11 proxy reply-framing discriminator

**Disposition:** `PASS_OFFLINE_STREAM_PARSER_CANDIDATE_SCOPED`.

This local check addresses the next discriminator named in the retained A02/A03
packet. It uses two synthetic X connections owned by the same PID, assigns
connection-local request sequences, parses complete X11 request/reply frame
lengths, and selects a single action-bound `GetPointerControl` reply on the
input connection. A same-PID
process-identity reply is forwarded even when the old coarse `input_started`
condition is true. The selected input reply is withheld only after a matching
KeyPress receipt for that action. Sequence equality without connection equality,
unknown sequence mappings, wrong PID, wrong action, absent KeyPress receipt, and
non-input request roles, or a mismatched keycode do not trigger withholding.

## Method and results

The frozen A03 predicate was replayed as a pure Boolean rule:

```text
owner PID matches AND response type is Reply AND input_started exists
```

For a pre-press `process_identity` reply from a second connection with the same
peer PID, that rule selects `hold`. This reproduces the suspected circular-gate
hazard at the predicate level. It does not prove which reply A03 actually saw:
the retained A03 raw does not have per-connection reply sequence evidence.

## Standard-caller source crosswalk

The current source identifies a narrower candidate reply than the first model
did:

1. On a guarded key-down, `_GuardedBackend._before_input_press` calls
   `_verify_process_identity_for_press` before dispatching input. When the query
   worker is enabled, `_read_process_identity` calls `_target_query`.
2. `TargetQueryWorker` runs its reader on a Python thread (same process PID),
   and the factory creates `X11TargetQueries`, whose constructor opens a new
   `display.Display`. This is a distinct X connection from the input backend
   connection, despite sharing the owner PID.
3. `X11Backend.key_state` then sends `xtest.fake_input(..., KeyPress, ...)` on
   the backend connection and calls `self.d.sync()`. The A03 lock pins
   `python-xlib==0.33`; that version's `Display.sync()` calls
   `get_pointer_control()`, a reply request with core opcode 106.
4. The frozen A03 proxy does not inspect client requests in its client-to-server
   relay. Its server-to-owner relay gates any reply from the owner PID after
   `input_started`; it has no connection/request-role selection. Thus a
   process-identity reply can be delayed before KeyPress, while the later input
   synchronization reply is not uniquely selected.

The revised offline model records the XTEST `FakeInput` KeyPress request and
the following `GetPointerControl` request on one connection, then correlates
their connection-local sequences with the reply. It deliberately gives a
second same-PID identity connection a reply with the same numeric sequence; that
identity reply is forwarded while only the input connection's target reply is
selected after a keycode/action-matched KeyPress receipt.

The follow-up [`proxy_candidate.py`](proxy_candidate.py) incrementally parses
fragmented X11 setup and request/reply streams for one connection. It negotiates
the XTEST major opcode from that connection's QueryExtension reply, tracks
connection-local request sequence and peer PID, and marks only the immediate
GetPointerControl following the negotiated XTEST KeyPress as a target candidate.
It fails open on unknown or ambiguous sequence mappings, mismatched identity,
missing independent keypress observation, wrong keycode/action, failed XTEST
negotiation, or an intervening request. Tests exercise little- and big-endian
setup, fragmented frames, same-PID connections with colliding sequence numbers,
wrong opcode/event, and fail-open cases. All 19 tests pass in normal and
optimized Python; outputs and package hashes are retained alongside this report.

This source crosswalk strengthens the circular-gate diagnosis but does not
recover the reply A03 actually saw: its first result has no per-connection
sequence trace. The parser is not connected to a socket relay and has no
independent application-event reader or bounded hold/release lifecycle. It
validates framing and selection policy only; it does not establish blocked-I/O
release, effect, recovery, or a live proxy result. Before any new live attempt,
integrate this parser into an isolated candidate relay, preserve explicit
connection IDs/PIDs and independent event receipt, and test EOF, server close,
sequence wrap, relay backpressure and owner retirement without changing A02/A03.
Request frames above the parser's 16 MiB bound raise `FrameError`; a future relay
must fail open to byte-preserving forwarding on parser limits/errors rather than
drop the client stream.
The wire layouts used here follow the [X11 Protocol specification](https://www.x.org/archive/current/doc/xproto/x11protocol.pdf)
and [XTEST Extension Protocol](https://www.x.org/releases/X11R7.7/doc/xextproto/xtest.pdf).

## Conditions and evidence

- Conditions: [`conditions.json`](conditions.json).
- Offline model: [`reply_gate.py`](reply_gate.py).
- Candidate stream parser: [`proxy_candidate.py`](proxy_candidate.py).
- Tests: [`test_reply_gate.py`](test_reply_gate.py) and
  [`test_proxy_candidate.py`](test_proxy_candidate.py).
- Source-chain audit: [`raw/source-chain-audit.json`](raw/source-chain-audit.json).
- Saved test output: [`raw/test-normal.txt`](raw/test-normal.txt) and
  [`raw/test-optimized.txt`](raw/test-optimized.txt).
- Candidate test output: [`raw/candidate-normal.txt`](raw/candidate-normal.txt)
  and [`raw/candidate-optimized.txt`](raw/candidate-optimized.txt).
- Baseline predicate replay: [`raw/legacy-gate-replay.json`](raw/legacy-gate-replay.json).
- Source hashes: [`SHA256SUMS`](SHA256SUMS).

No WSLc/Docker allocation, live X server, GUI, MCP server, OS input, or network
was used. A02 and A03 remain immutable and consumed; neither was rerun or
reinterpreted as a successful blocked trial. This result says nothing about
physical release, blocked-I/O cancellation, independent application effect,
bounded recovery, MAP01, or efficiency.

## Next decision

Build a test-only socket relay around this parser and add an independent
synthetic-event receipt path. Verify a blocked reply remains attributable to
the input connection while the process-identity reply is forwarded, then test
bounded owner retirement and release semantics with a fake upstream before
considering any WSLc-backed run. A03's raw lacks the needed sequence trace and
must remain unchanged. Issue #7924 currently holds WSLc at `STOP / HOLD`, so
this packet does not authorize a live attempt.

## Addendum — XRes wire and standard-caller composition r02 (2026-10-19)

The next construction step is now retained in
[`xres_wire_socket_r02/`](xres_wire_socket_r02/README.md). The standard
guarded-MCP caller's separate identity connection now sends serialized XRes
`QueryVersion` and `QueryClientIds` requests through `FakeSocketRelay`; the
synthetic server replies are decoded by python-xlib and the resulting PID feeds
the real process-generation digest path. The focused wire test passes 1/1 and
the caller composition suite passes 3/3 in normal and optimized Python. The
caller cases preserve generation-change refusal before KeyPress and `UNKNOWN`,
no-task-success, replay-disabled behavior after held input.

This closes the previously documented XRes wire-stub gap only for Fake X
construction. The server extension negotiation, process PID, `/proc`, and X11
server are synthetic; no live owner-disconnect or physical release was tested.
Issue #7924 remains `STOP / HOLD`; no WSLc allocation was checked or used, and
the consumed A02/A03 allocations were not rerun. First fixture parse failure
and corrected runs are preserved in the r02 packet's raw tree and SHA-256
manifest.
