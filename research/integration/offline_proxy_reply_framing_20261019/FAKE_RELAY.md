# Test-only socket relay result

**Disposition:** `PASS_FAKE_RELAY_CONSTRUCTION_SCOPED`.

This addendum completes the prior packet's next offline discriminator. It wraps
the existing X11 framing candidate with `fake_socket_relay.py` and three
process-local `socketpair()` channels: a caller stream, a fake upstream, and a
separate synthetic event-receipt channel. The relay accepts already-established
tracker state and opens no socket of its own.

## Observed behavior

- An ordinary unmatched `GetPointerControl` reply is forwarded when no matching
  independent event receipt exists.
- A separate receipt with the matching action ID, `KeyPress`, and keycode gates
  the selected reply. The relay buffers that reply and later server frames in
  stream order, then retires at the configured 150 ms deadline with
  `release_state=UNKNOWN`, `task_success=null`, and replay disabled.
- Fake-upstream EOF while a reply is held retires promptly with the same
  `UNKNOWN` terminal semantics. A non-reading client causes bounded
  `backpressure_limit` retirement. A 64 KiB valid server stream is forwarded
  intact when a client is actively draining it.
- Once a reply is held, a server parser error also keeps malformed later bytes
  behind it until timeout; parser fallback cannot reorder the stream.
- A malformed client frame disables parsing and preserves the exact bytes to
  the fake upstream. Parser/relay errors do not create a release or success
  claim.

Test-first regressions reproduced a false backpressure retirement on a large
but drainable stream, a stream-order violation where later server frames passed
a held reply, and a parser-error fallback that could bypass the hold. Each
pending buffer now flushes or retires at its configured bound. Once a reply is
held, all later frames, including malformed bytes, remain behind it until
retirement.

## Validation and limits

On Windows Python 3.11.9, the existing parser/specification tests plus the new
socket tests passed 27/27 in normal mode and 27/27 under `-O`. Exact output is
preserved in [`raw/fake-relay-test-normal.txt`](raw/fake-relay-test-normal.txt)
and [`raw/fake-relay-test-optimized.txt`](raw/fake-relay-test-optimized.txt);
conditions are in [`fake-relay-conditions.json`](fake-relay-conditions.json).
[`FAKE_RELAY_SHA256SUMS`](FAKE_RELAY_SHA256SUMS) binds the new sources, tests,
conditions, outputs, and parser implementation.

This is a local socket-pair construction test. It does not connect the relay to
the standard MCP caller or a real X server, inspect OS input state, establish
physical release, validate application effect, or prove a hard release-time
guarantee. `UNKNOWN` is the only terminal release classification when the
selected reply is withheld. It did not use WSLc, Docker, network access, a GUI,
OS input, a model, or a live allocation. A02/A03 and their first outcomes are
unchanged.

## Additive same-PID two-connection discriminator (2026-10-19)

The [two-connection r01 record](two-connection-r01/README.md) composes two
separate FakeSocketRelay channels with the same modeled owner PID and colliding
connection-local sequence 3. The pre-press identity-channel reply is forwarded;
only the input-channel reply following its own XTEST KeyPress and matching
synthetic event receipt is held. The held input stream retires as UNKNOWN. Its
28 parser/policy/socket cases and the standard-caller relay composition's three
cases pass in normal and optimized Python; exact outputs and source hashes are
in the additive packet.

The standard-caller suite now routes the caller's `TargetQueryWorker` process-
identity call through a second FakeSocketRelay, services three sequential
synthetic query/reply transactions, and verifies a changed fixture generation
is refused before input. The actual `X11TargetQueries.read` and process-identity
hash/validation code run against shaped synthetic XRes client-ID replies and a
fake `/proc` stat file. The socket adapter's NoOperation/GetPointerControl
frames are correlated test markers, not XRes wire encoding. This composes
caller→query-worker→identity-socket alongside the input socket and tests stale
generation refusal, but does not exercise actual XRes request/reply bytes or
live PID discovery. It preserves the existing late-request/UNKNOWN result and
does not establish physical release, task effect, or a WSLc result.

The later [standard-caller request-order R01 packet](standard-caller-order-r01/README.md)
repaired the composed Fake X test's actual `KeyPress → KeyRelease →
GetPointerControl` request order. It also corrected two scheduler-sensitive
test assumptions. The full CLI suite passes 593 tests (8 skipped), and the 48
focused parser/relay/composition/lifecycle/supervisor tests pass in normal and
optimized Python. These remain local synthetic checks; no live X server,
physical release, application task success, WSLc transfer or efficiency result
is established.

## Next boundary

Next, pass actual XRes QueryVersion/QueryClientIds request and reply frames over
the identity socket and into the Xlib decoder, retaining PID-namespace and
physical-release limits. Keep physical release and task success `UNKNOWN` until
the real backend has separate qualifying evidence. Do not attempt a live run
unless an unused allocation and the explicit WSLc owner gate are independently
verified.
